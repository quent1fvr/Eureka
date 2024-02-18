
import logging
import streamlit as st
from src.view.query_handler import SourceDisplay
class FeedbackHandler:
    @staticmethod
    def handle_feedback(feedback_type, feedback_content=""):
        FeedbackHandler.log_feedback(feedback_type, feedback_content)

    @staticmethod
    def log_feedback(feedback_type, feedback_content):
        if feedback_type == "Manual":
            logging.info(f"Feedback: {feedback_content} ", extra={'category': 'Manual Feedback', 'elapsed_time': 0})
        else:
            query, answer = "", ""
            sources_contents = [''] * 4
            if st.session_state['messages']:
                if len(st.session_state['messages']) > 1:
                    query = st.session_state['messages'][-2]["content"]
                    answer = st.session_state['messages'][-1]["content"]
                    sources_contents = SourceDisplay.get_sources_contents() if 'sources_info' in st.session_state else sources_contents
            logging.info(f"Feedback: {feedback_type}, Collection: Eureka, Query: {query}, Answer: {answer}, Sources: {sources_contents}", extra={'category': 'Thumb Feedback', 'elapsed_time': 0})

    @staticmethod
    def submit_manual_feedback(feedback_text):
        if feedback_text:
            FeedbackHandler.handle_feedback("Manual", feedback_text)

