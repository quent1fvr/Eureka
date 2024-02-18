from src.control.control import Chatbot
from src.data_processing.data_analyzer import DataAnalyzer
from src.data_processing.log_parser import LogParser
import streamlit as st
import os
logfile_path = os.getenv("LOGFILE_PATH")

class StreamlitInterfaceLOG:

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.log_parser = LogParser(log_file_path= logfile_path)
        self.data_analyzer = None
        self._setup_data()


    def _setup_data(self):
        df_logs = self.log_parser.read_and_parse_logs()
        df_logs_history = self.log_parser.read_and_parse_history_logs()
        df_feedback = self.log_parser.read_and_parse_feedback_logs()
        df_thumb_feedback = df_feedback[df_feedback['feedback_type'] == 'Thumb Feedback']
        df_manual_feedback = df_feedback[df_feedback['feedback_type'] == 'Manual Feedback']        
        self.data_analyzer = DataAnalyzer(df_logs, df_logs_history, df_feedback, df_thumb_feedback, df_manual_feedback)

    def generate_plots(self):
        fig1 = self.data_analyzer.plot_activity_over_time()
        fig2 = self.data_analyzer.plot_query_response_time()
        fig3 = self.data_analyzer.plot_success_vs_failure_rate()
        fig4 = self.data_analyzer.plot_activity_frequency_by_collection()
        fig5 = self.data_analyzer.plot_upload_times_analysis()
        fig7 = self.data_analyzer.query_answer_history()
        fig9 = self.data_analyzer.plot_feedback_analysis()
        fig10 = self.data_analyzer.plot_thumb_feedback_analysis()
        
        return fig1, fig2, fig3, fig4, fig5, fig7, fig9, fig10
    
    def refresh_plots(self):
        updated_plots = self.generate_plots()
        return updated_plots


    def gradio_interface(self):
        fig1, fig2, fig3, fig4, fig5, fig7, fig9, fig10 = self.generate_plots()
        return fig1, fig2, fig3, fig4, fig5, fig7, fig9, fig10  
    
    def log_view(self):
        st.title("Data Analysis Plots")

        fig1, fig2, fig3, fig4, fig5, fig7, fig9, fig10 = self.generate_plots()

        pages = {
            "Activity Over Time": fig1,
            "Query Response Time": fig2,
            "Success vs Failure Rate": fig3,
            "Activity Frequency by Collection": fig4,
            "Upload Times Analysis": fig5,
            "Query Answer History": fig7,
            "Feedback Analysis": fig9,
            "Thumb Feedback Analysis": fig10,
        }

        page = st.sidebar.selectbox("Choose a plot", list(pages.keys()))

        st.header(page)
        st.plotly_chart(pages[page])