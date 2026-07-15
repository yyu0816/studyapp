import streamlit as st

@st.dialog("Test")
def test_dialog():
    st.write("Hello")
    val = st.text_input("Hex", key="hex_in")
    html = """
    <input type="color" id="cp" value="%s">
    <script>
    const cp = document.getElementById('cp');
    cp.addEventListener('input', (e) => {
        const doc = window.parent.document;
        // Find the input by looking for aria-label or just the text input
        const inputs = doc.querySelectorAll('input[type="text"]');
        if (inputs.length > 0) {
            let target = inputs[inputs.length-1];
            target.value = e.target.value;
            target.dispatchEvent(new Event('input', {bubbles: true}));
            target.dispatchEvent(new Event('change', {bubbles: true}));
        }
    });
    </script>
    """ % (val or "#000000")
    st.components.v1.html(html, height=50)
    if st.button("Save"):
        st.write("Saved", val)

if st.button("Open"):
    test_dialog()
