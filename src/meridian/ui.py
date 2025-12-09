import streamlit as st
import sys
import os
import importlib.util
import inspect
import asyncio
from typing import Optional, List, Dict, Any
from meridian.core import FeatureStore

st.set_page_config(page_title="Meridian UI", page_icon="🧭", layout="wide")


def load_module_contents(
    file_path: str
) -> tuple[Optional[FeatureStore], Dict[str, Any], Dict[str, Any]]:
    """Load the module and find FeatureStore, Contexts, and Retrievers."""
    spec = importlib.util.spec_from_file_location("features", file_path)
    if not spec or not spec.loader:
        st.error(f"Could not load file: {file_path}")
        st.stop()

    module = importlib.util.module_from_spec(spec)
    sys.modules["features"] = module
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        st.error(f"Error loading module: {e}")
        return None, {}, {}

    store = None
    contexts = {}
    retrievers = {}

    # Inspect module
    for attr_name in dir(module):
        attr = getattr(module, attr_name)

        # Find Store
        if isinstance(attr, FeatureStore):
            store = attr

        # Find Contexts (decorated functions)
        if hasattr(attr, "_is_context") and attr._is_context:
            contexts[attr_name] = attr

        # Find Retrievers (decorated functions wrap Retriever logic)
        if hasattr(attr, "_meridian_retriever"):
            retrievers[attr_name] = getattr(attr, "_meridian_retriever")

    if not store:
        st.error("No FeatureStore instance found in the provided file.")
        st.stop()

    return store, contexts, retrievers


def render_context_tab(store: FeatureStore, contexts: Dict[str, Any]) -> None:
    st.header("Context Assembly")

    if not contexts:
        st.info("No @context functions found in this file.")
        return

    selected_ctx_name = st.selectbox("Select Context Definition", list(contexts.keys()))
    ctx_func = contexts[selected_ctx_name]

    st.markdown(f"**Function:** `{selected_ctx_name}`")
    if ctx_func.__doc__:
        st.caption(ctx_func.__doc__)

    # Dynamic Form based on Signature
    sig = inspect.signature(ctx_func)
    params = {}

    with st.form(key=f"ctx_form_{selected_ctx_name}"):
        st.subheader("Inputs")
        cols = st.columns(2)

        i = 0
        for name, param in sig.parameters.items():
            # Skip self/cls if any (shouldn't be for valid context func usually)
            if name in ["self", "cls"]:
                continue

            col = cols[i % 2]
            i += 1

            # Simple type inference for UI
            default = param.default if param.default != inspect.Parameter.empty else ""

            # Label with type hint if available
            label = f"{name}"
            if param.annotation != inspect.Parameter.empty:
                try:
                    label += f" ({param.annotation.__name__})"
                except Exception:
                    label += f" ({str(param.annotation)})"

            val = col.text_input(label, value=str(default) if default != "" else "")
            params[name] = val

        submitted = st.form_submit_button("Assemble Context", type="primary")

    if submitted:
        # Convert params and execute
        try:
            # Basic type coercion could go here, for now passing strings
            # (Meridian Pydantic models usually handle parsing if typed properly,
            # but function args might need manual conversion if int/bool expected)

            with st.spinner("Assembling Context..."):
                # Inject store backend if not present (UI harness magic)
                # The @context wrapper handles finding store if passed, but here we invoke directly.
                # Inspect func to see if it needs store passed explicitly?
                # Usually @context(store=...) handles it.

                # Check for async
                if inspect.iscoroutinefunction(ctx_func):
                    result = asyncio.run(ctx_func(**params))
                else:
                    # Wrapped context should be async usually, but if wrapper handles sync?
                    # The wrapper in context.py is async `async def wrapper`
                    # So we must await it.
                    result = asyncio.run(ctx_func(**params))

            # Render Result
            st.success(f"Context Assembled: {result.id}")

            # Metrics
            m_cols = st.columns(4)
            m_cols[0].metric(
                "Token Usage",
                result.meta.get("token_usage", result.meta.get("usage", "N/A")),
            )
            m_cols[1].metric("Cost (USD)", f"${result.meta.get('cost_usd', 0):.6f}")
            m_cols[2].metric(
                "Latency",
                f"{result.meta.get('latency_ms', 0):.2f}ms"
                if "latency_ms" in result.meta
                else "N/A",
            )
            m_cols[3].metric("Freshness", result.meta.get("freshness_status", "N/A"))

            # HTML Repr
            st.markdown(result._repr_html_(), unsafe_allow_html=True)

            # Json Dump for debug
            with st.expander("Raw JSON"):
                st.json(result.model_dump())

        except Exception as e:
            st.error(f"Assembly Failed: {str(e)}")


def main(args: Optional[List[str]] = None) -> None:
    st.title("🧭 Meridian Feature Store")

    if args is None:
        args = sys.argv

    if len(args) < 2:
        st.warning("Please provide the path to your feature definition file.")
        st.info("Usage: meridian ui <path_to_features.py>")
        return

    feature_file = args[1]

    if not os.path.exists(feature_file):
        st.error(f"File not found: {feature_file}")
        return

    store, contexts, retrievers = load_module_contents(feature_file)
    if store is None:
        return

    # Sidebar
    st.sidebar.header("Configuration")
    st.sidebar.text(f"Loaded: {os.path.basename(feature_file)}")

    # Retrievers List in Sidebar
    if retrievers:
        st.sidebar.subheader("Retrievers")
        for r_name, r_obj in retrievers.items():
            st.sidebar.markdown(
                f"- **{r_name}**: `{r_obj.backend}` (TTL: {r_obj.cache_ttl})"
            )

    # Tabs
    tab1, tab2 = st.tabs(["Store & Features", "Context Assembly"])

    with tab1:
        render_feature_tab(store)

    with tab2:
        render_context_tab(store, contexts)


def render_feature_tab(store: FeatureStore) -> None:
    entities = list(store.registry.entities.keys())
    if not entities:
        st.warning("No entities found in the Feature Store.")
        return

    # Visual Eureka: Dependency Graph
    with st.expander("🗺️ Feature System Map", expanded=True):
        import streamlit.components.v1 as components

        # Build Mermaid Graph
        graph = ["graph LR"]
        graph.append(
            "    classDef entity fill:#e1f5fe,stroke:#01579b,stroke-width:2px;"
        )
        graph.append(
            "    classDef feature fill:#fff3e0,stroke:#ff6f00,stroke-width:1px;"
        )
        graph.append("    classDef store fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;")

        # Online Store Node
        os_type = store.online_store.__class__.__name__
        graph.append(f"    OS[({os_type})]")
        graph.append("    class OS store;")

        for name, ent in store.registry.entities.items():
            safe_name = name.replace(" ", "_")
            ent_id = f"ENT_{safe_name}"
            graph.append(f"    subgraph {safe_name}")
            graph.append(f"        {ent_id}[{name}]")
            graph.append(f"        class {ent_id} entity;")

            # Find features for this entity
            feats = store.registry.get_features_for_entity(name)
            for f in feats:
                safe_feat = f.name.replace(" ", "_")
                feat_node = f"FEAT_{safe_feat}"
                graph.append(f"        {feat_node}({f.name})")
                graph.append(f"        class {feat_node} feature;")
                graph.append(f"        {ent_id} --> {feat_node}")

                if f.materialize:
                    graph.append(f"        {feat_node} -. Materialize .-> OS")

            graph.append("    end")

        mermaid_code = "\n".join(graph)

        html = f"""
        <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        </script>
        <div class="mermaid">
        {mermaid_code}
        </div>
        """
        components.html(html, height=300, scrolling=True)

    selected_entity_name = st.selectbox("Select Entity", entities)
    entity = store.registry.entities[selected_entity_name]

    # Main Content
    st.subheader(f"Entity: {selected_entity_name}")
    st.markdown(f"**ID Column:** `{entity.id_column}`")
    if entity.description:
        st.markdown(f"_{entity.description}_")

    # Input ID
    entity_id = st.text_input(f"Enter {entity.id_column}", value="u1")

    # Custom Styling
    st.markdown(
        """
        <style>
        div[data-testid="metric-container"] {
            background-color: var(--secondary-background-color, #f0f2f6);
            border: 1px solid var(--text-color-20, #e0e0e0);
            padding: 15px;
            border-radius: 10px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        }
        div[data-testid="metric-container"] label {
            font-weight: bold;
            color: var(--text-color, #333);
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    if st.button("Fetch Features", type="primary"):
        with st.spinner("Fetching features..."):
            # Get all features for this entity
            features = store.registry.get_features_for_entity(selected_entity_name)
            feature_names = [f.name for f in features]

            if not feature_names:
                st.warning("No features defined for this entity.")
            else:
                # Fetch values
                values = asyncio.run(
                    store.get_online_features(
                        entity_name=selected_entity_name,
                        entity_id=entity_id,
                        features=feature_names,
                    )
                )

                # Display as Metrics Cards
                st.subheader("Feature Values")

                # Create 3 columns for grid layout
                cols = st.columns(3)

                for i, feat in enumerate(features):
                    val = values.get(feat.name)
                    col = cols[i % 3]

                    # Determine delta color if relevant (mock logic)
                    delta = None
                    if isinstance(val, (int, float)) and val > 50:
                        delta = "High"

                    col.metric(
                        label=feat.name,
                        value=str(val),
                        delta=delta,
                        help=f"Type: {feat.func.__annotations__.get('return', 'Any').__name__ if hasattr(feat.func.__annotations__.get('return'), '__name__') else str(feat.func.__annotations__.get('return', 'Any'))}\nRefresh: {feat.refresh}",
                    )

                # Display detailed view below
                with st.expander("Feature Definition Details"):
                    st.json(
                        [
                            {
                                "name": f.name,
                                "refresh": f.refresh,
                                "ttl": str(f.ttl),
                                "materialize": f.materialize,
                            }
                            for f in features
                        ]
                    )


if __name__ == "__main__":
    main()
