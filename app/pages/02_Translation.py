import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import plotly.express as px
from annotated_text import annotated_text 

from utils import *
from bootstraping import *

DATA_PATH_csv = './results_summary/results_summary.csv'
DATA_PATH = './results'

INVALID_LOW = -1000
INVALID_HIGH = 1000

def main():

    st.set_page_config(page_title="Translation", page_icon="🔎", layout="wide")

    if os.path.exists(DATA_PATH_csv):
        # Load the dataset
        df = pd.read_csv(DATA_PATH_csv)

        # Column layout for the select boxes
        col1, col2, col3 = st.columns(3)
        # Dataset Selection

        datasets_mt = [dataset for dataset in df['dataset'].unique() if is_valid_mt_dataset(dataset)]

        with col1:
            dataset_selected = st.selectbox('Select Dataset', datasets_mt)
        # Filter the DataFrame based on the selected dataset
        filtered_df_by_dataset = df[df['dataset'] == dataset_selected]
        # Source Language Selection (dependent on the selected dataset)
        with col2:
            source_selected = st.selectbox(
                'Select Source Language', 
                sorted( filtered_df_by_dataset['source'].unique() )
            )
        # Filter the DataFrame based on the selected dataset and source
        filtered_df_by_source = filtered_df_by_dataset[filtered_df_by_dataset['source'] == source_selected]
        # Target Language Selection (dependent on the selected dataset and source)
        with col3:
            target_selected = st.selectbox(
                'Select Target Language', 
                sorted( filtered_df_by_source['target'].unique() )
            )
        # Filter the DataFrame based on all selections
        final_filtered_df = filtered_df_by_source[filtered_df_by_source['target'] == target_selected]

        # Display the filtered rows
        st.write('Filtered Rows:')
        st.dataframe(final_filtered_df)

        JSONS = []
        NAMES = []
        if not final_filtered_df.empty:    
            for index, row in final_filtered_df.iterrows():
                # Get the model_name and file_name
                model_name = row['model_name']
                file_name = row['file_name']
                
                file_path = os.path.join(DATA_PATH, model_name, file_name)
                JSONS.append(file_path)
                NAMES.append(model_name)
        else:
            st.write('No data available for the selected combination.')

        # Load the JSON data
        def load_data(json_path):
            with open(json_path, 'r', encoding='utf8') as f:
                data = json.load(f)
            first_key = next(iter(data['results']))
            return data['results'][first_key]

        selected_models = st.multiselect('Select models to compare', options = NAMES)
        
        # load models data
        DATA_MODELS = {}

        for modelname, json_path in zip(NAMES, JSONS):
            if modelname in selected_models:
                data = load_data(json_path)
                # Extract corpus-level metrics, if they are not computed, 
                # then assign the corresponding default value, -1000 for 
                # high is better, +1000 for lower is better metrics

                bleu_corpus = data.get('bleu,none', -1000)
                ter_corpus = data.get('ter,none', 1000)
                chrf_corpus = data.get('chrf,none', -1000)
                comet_corpus = data.get('comet,none', -1000)
                cometkiwi_corpus = data.get('comet_kiwi,none', -1000)
                bleurt_corpus = data.get('bleurt,none', -1000)
                xcomet_corpus = data.get('xcomet,none', -1000)
                metricx_corpus = data.get('metricx,none', -1000)
                metricx_qe_corpus = data.get('metricx_qe,none', -1000)

                # Extract segment-level data
                bleu_segments = data.get('bleu_segments,none', [])
                comet_segments = data.get('comet_segments,none', [])
                comet_kiwi_segments = data.get('comet_kiwi_segments,none', [])
                metricx_qe_segments = data.get('metricx_qe_segments,none', [])
                metricx_segments = data.get('metricx_segments,none', [])
                sources = data.get('sources,none', [])  # Sources of each segment
                targets = data.get('targets,none', [])  # Targets of each segment
                translations = data.get('translations,none', [])  # Translations generated by the model

                # Extract xcometxl error spans
                xcometxl_error_spans = data.get('xcomet_error_spans,none', [])

                DATA_MODELS[modelname] = {  
                                            # metrics
                                            'bleu':bleu_corpus, 'ter':ter_corpus, 'chrf':chrf_corpus, 
                                            'comet': comet_corpus, 'comet-kiwi': cometkiwi_corpus, 'bleurt': bleurt_corpus,
                                            'metricx': metricx_corpus, 'metricx_qe': metricx_qe_corpus, 'xcomet': xcomet_corpus,
                                            # text
                                            'sources':sources, 'targets': targets, 'translations': translations, 
                                            # segments
                                            'bleu_segments': bleu_segments, 
                                            'comet_segments': comet_segments,
                                            'comet_kiwi_segments': comet_kiwi_segments,
                                            'metricx_segments': metricx_segments,
                                            'metricx_qe_segments': metricx_qe_segments,
                                            # error spans
                                            'xcometxl_error_spans': xcometxl_error_spans
                                        }

        # Tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Corpus-Level Metrics", 
            "Data Visualization", 
            "Detailed Segment View",
            "Interactive Table",
            "Pairwise comparisons",
            "Errors",
            "Lengths"
        ])

        with tab1:
            
            if DATA_MODELS:
                st.divider()

                # List of available metrics
                AVAILABLE_METRICS = ['bleu', 'ter', 'chrf', 'comet', 'comet-kiwi', 'bleurt', 'metricx', 'metricx_qe', 'xcomet']

                # Precompute the best metrics
                best_metrics = {
                    "bleu": max(data_model['bleu'] for data_model in DATA_MODELS.values()),
                    "ter": min(data_model['ter'] for data_model in DATA_MODELS.values()),
                    "chrf": max(data_model['chrf'] for data_model in DATA_MODELS.values()),
                    "comet": max(data_model['comet'] for data_model in DATA_MODELS.values()),
                    "comet-kiwi": max(data_model['comet-kiwi'] for data_model in DATA_MODELS.values()),
                    "bleurt": max(data_model['bleurt'] for data_model in DATA_MODELS.values()),
                    "metricx": min(data_model['metricx'] for data_model in DATA_MODELS.values()),
                    "metricx_qe": min(data_model['metricx_qe'] for data_model in DATA_MODELS.values()),
                    "xcomet": max(data_model['xcomet'] for data_model in DATA_MODELS.values())
                }


                # Allow the user to select which metrics to display
                selected_metrics = st.multiselect(
                    'Select metrics to display:', 
                    options=AVAILABLE_METRICS, 
                    default=['bleu', 'ter', 'chrf', 'comet', 'comet-kiwi', 'bleurt']
                )

                # Helper function to calculate delta and decide display logic
                def display_metric(column, name, value, best_value, inverse=False):
                    if value == INVALID_LOW or value == INVALID_HIGH:
                        column.metric(name, None, delta=None, delta_color='off')
                        return

                    delta = round(value - best_value, 3)
                    is_best = delta == 0

                    delta_value = delta if not is_best else 'BEST'
                    if delta < 0 and not inverse:
                        delta_color = 'normal'
                    elif delta > 0 and inverse:
                        delta_color = 'inverse'
                    else:
                        delta_color = 'off'

                    column.metric(name, round(value, 2), delta=delta_value, delta_color=delta_color)

                st.divider()
                # Loop through each model and display the selected metrics
                for modelname, data_model in DATA_MODELS.items():
                    st.markdown(f'###### **{modelname}**')
                    cols = st.columns(max(len(selected_metrics), 1))
                    
                    # Conditional display of selected metrics
                    for idx, metric in enumerate(selected_metrics):
                        if metric == 'bleu':
                            display_metric(cols[idx], "BLEU", data_model['bleu'], best_metrics['bleu'])
                        elif metric == 'ter':
                            display_metric(cols[idx], "TER", data_model['ter'], best_metrics['ter'], inverse=True)
                        elif metric == 'chrf':
                            display_metric(cols[idx], "ChrF", data_model['chrf'], best_metrics['chrf'])
                        elif metric == 'comet':
                            display_metric(cols[idx], "COMET", data_model['comet'], best_metrics['comet'])
                        elif metric == 'comet-kiwi':
                            display_metric(cols[idx], "COMET-KIWI", data_model['comet-kiwi'], best_metrics['comet-kiwi'])
                        elif metric == 'bleurt':
                            display_metric(cols[idx], "BLEURT", data_model['bleurt'], best_metrics['bleurt'])
                        elif metric == 'metricx':
                            display_metric(cols[idx], "METRICX", data_model['metricx'], best_metrics['metricx'], inverse=True)
                        elif metric == 'metricx_qe':
                            display_metric(cols[idx], "METRICX-QE", data_model['metricx_qe'], best_metrics['metricx_qe'], inverse=True)
                        elif metric == 'xcomet':
                            display_metric(cols[idx], "X-COMET", data_model['xcomet'], best_metrics['xcomet'])

                    st.divider()

            else:
                st.warning("Corpus-Level Metrics require data from at least one model. Please select a model to proceed.")

        with tab2:
            st.subheader("Data Visualization")
            
            if DATA_MODELS:
                metric_selected = st.selectbox("Select Metric for Visualization", ["bleu_segments", "comet_segments", "comet_kiwi_segments", 
                                                                                "metricx_qe_segments", "metricx_segments"])
                data_for_plot = []

                # Collect segment-level data for all models
                for modelname, data_model in DATA_MODELS.items():
                    if len(data_model[metric_selected]) > 0:
                        
                        rows = [(modelname, score, i) for i, score in enumerate(data_model[metric_selected])]

                        data_for_plot.extend(rows)
                
                # Convert to DataFrame for Plotly
                plot_df = pd.DataFrame(data_for_plot, columns=['Model', metric_selected, 'Index'])
                # Create an interactive box plot with Plotly
                fig = px.box(plot_df, x='Model', y=metric_selected, points="all", hover_data=['Index'], 
                            title=f'{metric_selected} Scores Distribution Across Models')

                st.plotly_chart(fig)
            else:
                st.warning("No data available for visualization.")


        with tab3:
            st.subheader("Detailed Segment View")
            
            if DATA_MODELS:
                detailed_data = DATA_MODELS[list(DATA_MODELS.keys())[0]]
                show_annot = st.toggle('Show error spans if available', value=True)

                if len(detailed_data['sources']) > 0:
                    segment_index = st.number_input(
                        "Select Segment Index", 
                        min_value=0, 
                        max_value=len(detailed_data['sources']) - 1, 
                        value=0, 
                        step=1
                    )

                    st.write(f"**Source Sentence:** {detailed_data['sources'][segment_index]}")
                    st.write(f"**Target Sentence:** {detailed_data['targets'][segment_index]}")

                    st.divider()
                    # Display translations from all models
                    for modelname, data_model in DATA_MODELS.items():
                        st.markdown(f"Model: {modelname}")
                        if len(data_model['translations']) > 0:

                            if len(data_model['xcometxl_error_spans']) > 0 and show_annot:
                                errors = data_model['xcometxl_error_spans'][segment_index]
                                translation = data_model['translations'][segment_index]
                                annotated_translation = process_sentence(translation, errors)
                                st.write("**Translation:** ")
                                annotated_text(annotated_translation)
                            
                            else:
                                st.write(f"**Translation:** {data_model['translations'][segment_index]}")
                            
                            bleu_score_index = get_score(data_model['bleu_segments'], segment_index)
                            comet_score_index = get_score(data_model['comet_segments'], segment_index)
                            comet_kiwi_score_index = get_score(data_model['comet_kiwi_segments'], segment_index)
                            st.write("BLEU Score", bleu_score_index, "COMET Score", comet_score_index, "COMET-KIWI Score", comet_kiwi_score_index )
                        
                        else:
                            st.markdown('Translations are not available')
                        st.divider()
            else:
                st.warning("No data available for detailed segment view.")


        # Interactive Table
        with tab4:
            st.subheader("Interactive Table")
            
            if DATA_MODELS:
                all_segment_data = []
                
                # Collect all data into a single DataFrame
                for modelname, data_model in DATA_MODELS.items():
                    num_segments = len(data_model['bleu_segments'])
                    for i in range(num_segments):
                        all_segment_data.append({
                            'Model': modelname,
                            'Source': get_string( data_model['sources'], i),
                            'Target': get_string( data_model['targets'], i),
                            'Translation': get_string( data_model['translations'], i),
                            'BLEU': get_score( data_model['bleu_segments'], i),
                            'COMET': get_score(data_model['comet_segments'], i),
                            'COMET-KIWI':  get_score(data_model['comet_kiwi_segments'], i )
                        })
                
                segment_df = pd.DataFrame(all_segment_data)
                st.dataframe(segment_df)

            else:
                st.warning("No data available for interactive table.")

        with tab5:
            st.subheader("Pairwise comparisons")

            if DATA_MODELS and len(list(DATA_MODELS.keys())) >= 2:
                system1_col, system2_col, metric_col = st.columns(3)
                available_models = list(DATA_MODELS.keys())
                with system1_col:
                    system1 = st.selectbox('System 1', options = available_models  ) 
                with system2_col:
                    system2 = st.selectbox('System 2', options =[model for model in available_models if model != system1] ) 
                with metric_col:
                    metric_pairwise = st.selectbox( 'Metric', options = ["bleu_segments", "comet_segments", "comet_kiwi_segments" ] )
                fig_segment_pairwise = plot_segment_pairwise(DATA_MODELS, system1, system2, metric_pairwise)
                if fig_segment_pairwise is not None:
                    st.plotly_chart(fig_segment_pairwise)
                else:
                    st.warning(f'No data available for {metric_pairwise}')

                ################ Bootsraping ################

                # Get the segment-level scores
                system1_scores = DATA_MODELS.get(system1, {}).get(metric_pairwise)
                system2_scores = DATA_MODELS.get(system2, {}).get(metric_pairwise)

                # Check if scores are available
                if system1_scores is None or system2_scores is None:
                    st.error("Scores are not available for one or both systems.")
                elif len(system1_scores) != len(system2_scores) or len(system1_scores) == 0:
                    st.warning("Segment-level scores are not available or lengths do not match.")
                else:
                    # Compute bootstrap test
                    results = compute_bootstrap_test(system1_scores, system2_scores, metric_pairwise)

                    # Extract the results
                    result_metric = results[metric_pairwise]
                    result_sys1 = result_metric[0]
                    result_sys2 = result_metric[1]

                    # Prepare data for display
                    data = {
                        'System': [system1, system2],
                        'Score': [f"{result_sys1.score:.3f}", f"{result_sys2.score:.3f}"],
                        'Mean': [f"{result_sys1.mean:.3f}", f"{result_sys2.mean:.3f}"],
                        'CI': [f"±{result_sys1.ci:.3f}", f"±{result_sys2.ci:.3f}"]
                    }

                    df_results = pd.DataFrame(data)

                    # Display the results
                    st.markdown(f"Bootstrap Test Results for **{metric_pairwise}**")
                    st.table(df_results)

                    # Display the p-value
                    p_value = result_sys2.p_value
                    st.write(f"**P-value:** {p_value:.4g}")

                    # Interpret the p-value
                    if p_value < 0.05:
                        st.success("The difference is **statistically significant**.")
                    else:
                        st.info("The difference is **not statistically significant**.")

                ################ Bootsraping ################

            else:
                st.warning("Pairwise comparisons require data from at least two models. Please select two or more models to proceed.")


        with tab6:

            st.subheader("Errors")

            if DATA_MODELS:

                stacked_bar_chart_data = {}
                for modelname, data_model in DATA_MODELS.items():
                    if len(data_model['xcometxl_error_spans']) > 0:
                        minor_count, major_count, critical_count = count_errors(data_model['xcometxl_error_spans'])
                        stacked_bar_chart_data[modelname] = {'minor': minor_count, 'major': major_count, 'critical': critical_count}
                fig_stacked_bar_chart = create_stacked_bar_chart(stacked_bar_chart_data)
                st.plotly_chart(fig_stacked_bar_chart)
                
            else:
                st.warning("No data available for errors. Please select a model to proceed.")

        with tab7:

            st.subheader("Lengths")

            if DATA_MODELS:
                
                # Let user select the metric to analyze
                metric_selected = st.selectbox(
                    "Select Metric for Length Analysis", 
                    ["bleu_segments", "comet_segments", "comet_kiwi_segments"]
                )
                
                # Collect data for all models
                length_data = []

                for modelname, data_model in DATA_MODELS.items():
                    sources = data_model.get('sources', [])
                    metric_scores = data_model.get(metric_selected, [])
                    num_segments = min(len(sources), len(metric_scores))
                    for i in range(num_segments):
                        source_length = len(sources[i].split())
                        metric_score = metric_scores[i]
                        length_data.append({
                            'Model': modelname,
                            'Source Length': source_length,
                            'Metric Score': metric_score,
                            'Index': i
                        })
                
                # Create DataFrame
                length_df = pd.DataFrame(length_data)

                if not length_df.empty:

                    # Plot the relationship between source length and metric score
                    fig = px.scatter(
                        length_df, 
                        x='Source Length', 
                        y='Metric Score', 
                        color='Model',
                        title=f'{metric_selected} vs. Source Length',
                        hover_data=['Index']
                    )

                    st.plotly_chart(fig)

            else:
                st.warning("No data available for lengths analysis.")

    else:
        st.error(f"File not found: {DATA_PATH_csv}. Please ensure the file exists.")

if __name__ == "__main__":
    main()