import streamlit as st
import sys
import os

# Allow app.py to import files from src folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.predict import predict_message
from src.predict_type import predict_scam_type
from src.explanation import generate_explanation, generate_safety_advice
from src.url_features import analyze_urls_in_message


def calculate_final_risk(message_risk_score, url_results):
    """
    Combines message-based AI risk and URL-based risk.
    Message model = 70%
    URL analyzer = 30%
    """

    max_url_risk = 0

    if url_results:
        max_url_risk = max(item["url_risk_score"] for item in url_results)

    final_risk_score = round((message_risk_score * 0.7) + (max_url_risk * 0.3), 2)

    if final_risk_score >= 75:
        final_risk_level = "High Risk"
    elif final_risk_score >= 45:
        final_risk_level = "Medium Risk"
    else:
        final_risk_level = "Low Risk"

    return final_risk_score, final_risk_level


st.set_page_config(
    page_title="ScamShield AI",
    page_icon="🛡️",
    layout="centered"
)

st.title("🛡️ ScamShield AI")
st.subheader("Explainable Multi-Channel Digital Scam Detection System")

st.write(
    "Paste a suspicious SMS, WhatsApp, Telegram, email, or social media message below. "
    "The system will analyze the message text, detect URLs, predict scam risk, "
    "identify scam type, and explain the warning signs."
)

message = st.text_area("Enter message here:", height=180)

if st.button("Analyze Message"):
    if not message.strip():
        st.warning("Please enter a message first.")

    else:
        # 1. Main message prediction: safe / suspicious / scam
        result = predict_message(message)

        # 2. Scam type prediction
        type_result = predict_scam_type(message)

        # 3. Rule-based explanation
        explanation = generate_explanation(message)

        # 4. URL risk analysis
        url_results = analyze_urls_in_message(message)

        # 5. Final combined risk score
        final_risk_score, final_risk_level = calculate_final_risk(
            result["risk_score"],
            url_results
        )

        # 6. Safety advice
        advice = generate_safety_advice(
            result["prediction"],
            final_risk_level
        )

        st.markdown("---")

        st.subheader("Final Prediction Result")

        if final_risk_score >= 75 or result["prediction"] == "scam":
            st.error("Prediction: Scam / High Suspicion")
        elif final_risk_score >= 45 or result["prediction"] == "suspicious":
            st.warning("Prediction: Suspicious")
        else:
            st.success("Prediction: Likely Safe")

        st.metric("Final Risk Score", f"{final_risk_score}%")
        st.write(f"**Final Risk Level:** {final_risk_level}")

        st.write(f"**Detected Scam Type:** {type_result['scam_type'].title()}")
        st.write(f"**Scam Type Confidence:** {type_result['confidence']}%")

        st.markdown("---")

        st.subheader("Message AI Analysis")

        st.write(f"**Text Model Prediction:** {result['prediction'].capitalize()}")
        st.metric("Message Risk Score", f"{result['risk_score']}%")
        st.write(f"**Message Risk Level:** {result['risk_level']}")

        with st.expander("View Class Probabilities"):
            for label, probability in result["probabilities"].items():
                st.write(f"**{label.capitalize()}:** {round(probability * 100, 2)}%")

        st.markdown("---")

        st.subheader("Why did the system say this?")

        for item in explanation:
            st.write(f"- {item}")

        st.markdown("---")

        st.subheader("URL Risk Analysis")

        if url_results:
            for url_result in url_results:
                st.write(f"**Detected URL:** {url_result['url']}")
                st.metric("URL Risk Score", f"{url_result['url_risk_score']}%")

                st.write("**URL Risk Factors:**")
                for factor in url_result["url_risk_factors"]:
                    st.write(f"- {factor}")

                st.write("")
        else:
            st.info("No URL detected in this message.")

        st.markdown("---")

        st.subheader("Safety Recommendation")

        for item in advice:
            st.write(f"- {item}")

st.markdown("---")

st.caption(
    "Disclaimer: ScamShield AI is a decision-support tool. "
    "It does not guarantee perfect detection. Always verify suspicious messages "
    "through official websites, verified pages, hotlines, or trusted authorities."
)