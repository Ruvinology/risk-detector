import streamlit as st
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.service import analyze_message

if "message_count" not in st.session_state:
    st.session_state.message_count = 0


def _delivery_action(result):
    if "delivery_action" in result:
        return result["delivery_action"]

    verdict = result.get("verdict", "")
    if verdict == "Scam / High Suspicion":
        return "block"
    if verdict == "Suspicious":
        return "warn"
    return "allow"


st.set_page_config(
    page_title="ScamShield AI",
    page_icon="app/assets/logo.svg",
    layout="centered",
)

st.sidebar.header("Settings")
training_mode = st.sidebar.toggle(
    "Training mode",
    value=True,
    help="When on, lets you report incorrect scans for model retraining.",
)

if training_mode:
    st.sidebar.caption("Use “Report incorrect result” after any analysis.")
else:
    st.sidebar.caption("Training prompts disabled.")

st.title("ScamShield AI")
st.subheader("Explainable Multi-Channel Digital Scam Detection System")

st.write(
    "Paste a suspicious SMS, WhatsApp, Telegram, email, or social media message below. "
    "The system analyzes message text, detects URLs, predicts scam risk, "
    "identifies scam type, and explains the warning signs."
)

message = st.text_area("Enter message here:", height=180)

if st.button("Analyze Message"):
    if not message.strip():
        st.warning("Please enter a message first.")
    else:
        try:
            result = analyze_message(message)
        except ValueError as exc:
            st.warning(str(exc))
        except FileNotFoundError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
        else:
            msg = result["message_analysis"]
            scam_type = result["scam_type"]
            action = _delivery_action(result)

            st.markdown("---")
            st.subheader("Final Prediction Result")

            if action == "block":
                st.error(f"Final verdict: {result['verdict']}")
            elif action == "warn":
                st.warning(f"Final verdict: {result['verdict']}")
            else:
                st.success(f"Final verdict: {result['verdict']}")

            col1, col2, col3 = st.columns(3)
            col1.metric("Final Risk Score", f"{result['final_risk_score']}%")
            col2.metric("Risk Level", result["final_risk_level"])
            col3.metric("Delivery Action", action.upper())

            st.caption(
                "Delivery action is what a chat app would do: "
                "ALLOW = deliver, WARN = show caution, BLOCK = freeze message."
            )

            st.write(f"**Detected Scam Type:** {scam_type['scam_type'].title()}")
            st.write(f"**Scam Type Confidence:** {scam_type['confidence']}%")

            st.markdown("---")
            st.subheader("Message AI Analysis")

            st.write(f"**Text Model Prediction:** {msg['prediction'].capitalize()}")
            st.metric("Message Risk Score", f"{msg['risk_score']}%")
            st.write(f"**Message Risk Level:** {msg['risk_level']}")

            with st.expander("View Class Probabilities"):
                for label, probability in msg["probabilities"].items():
                    st.write(f"**{label.capitalize()}:** {probability}%")

            st.markdown("---")
            st.subheader("Why did the system say this?")

            for item in result["explanation"]:
                st.write(f"- {item}")

            st.markdown("---")
            st.subheader("URL Risk Analysis")

            if result["url_analysis"]:
                for url_result in result["url_analysis"]:
                    trusted = url_result.get("trusted", False)
                    status = "Trusted domain" if trusted else "Untrusted domain"
                    st.write(f"**Detected URL:** {url_result['url']} ({status})")
                    st.metric("URL Risk Score", f"{url_result['url_risk_score']}%")

                    st.write("**URL Risk Factors:**")
                    for factor in url_result["url_risk_factors"]:
                        st.write(f"- {factor}")

                    st.write("")
            else:
                st.info("No URL detected in this message.")

            st.markdown("---")
            st.subheader("Safety Recommendation")

            for item in result["safety_advice"]:
                st.write(f"- {item}")

            st.session_state.message_count += 1

            if training_mode:
                with st.expander("Report incorrect result"):
                    wrong_label = st.selectbox(
                        "Correct label:",
                        ["", "safe", "suspicious", "scam"],
                        key=f"fb_{st.session_state.message_count}",
                    )
                    if st.button(
                        "Submit correction",
                        icon=":material/flag:",
                        key=f"fb_submit_{st.session_state.message_count}",
                    ):
                        if not wrong_label:
                            st.warning("Select the correct label first.")
                        else:
                            from src.feedback import save_feedback

                            save_feedback(
                                message=message,
                                predicted_action=action,
                                predicted_verdict=result["verdict"],
                                user_rating="wrong",
                                correct_label=wrong_label,
                                source="streamlit",
                            )
                            st.success("Correction saved for retraining.")

st.markdown("---")

st.caption(
    "Disclaimer: ScamShield AI is a decision-support tool. "
    "It does not guarantee perfect detection. Always verify suspicious messages "
    "through official websites, verified pages, hotlines, or trusted authorities."
)
