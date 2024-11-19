import streamlit as st
import pandas as pd
import os
import json
from utils import get_string, get_score

DATA_PATH_csv = './results_summary/results_summary.csv'
DATA_PATH = './results'

INVALID_LOW = -1000
INVALID_HIGH = 1000

def main():
    
    st.set_page_config(page_title="Added Toxicity", page_icon="🔎", layout="wide")

    if os.path.exists(DATA_PATH_csv):
        # Load the dataset
        df = pd.read_csv(DATA_PATH_csv)

        col1, col2 = st.columns(2)
        axis_available = ['others_hb', 'ability_hb', 'age_hb', 'body_type_hb', 'characteristics_hb', 'cultural_hb', 'gender_and_sex_hb', 'nationality_hb', 
                        'nonce_hb', 'political_ideologies_hb', 'race_ethnicity_hb', 'religion_hb', 'sexual_orientation_hb', 'socioeconomic_class_hb']
        # axis selection
        with col1:
            axis_selected = st.selectbox('Select Axis', axis_available)
        # Filter the DataFrame based on the selected dataset
        filtered_df_by_dataset = df[df['dataset'] == axis_selected]
        # Source Language Selection (dependent on the selected dataset)
        with col2:
            target_selected = st.selectbox(
                'Select Target Language', 
                sorted( filtered_df_by_dataset['target'].unique() )
            )
        filtered_df_by_target = filtered_df_by_dataset[filtered_df_by_dataset['target'] == target_selected]
        
        # Display the filtered rows
        st.write('Filtered Rows:')
        st.dataframe(filtered_df_by_target)


        JSONS = []
        NAMES = []
        if not filtered_df_by_target.empty:    
            for index, row in filtered_df_by_target.iterrows():
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

                cometkiwi_etox = data.get('comet_kiwi_etox,none', -1000)
                cometkiwi_mutox = data.get('comet_kiwi_mutox,none', -1000)
                n_sentences = data.get('n_sentences,none', -1000)
                etox = data.get('etox,none', 1000)
                mutox = data.get('mutox,none', 1000)

                # Extract segment-level data
                sources = data.get('sources,none', [])  # Sources of each segment
                translations = data.get('translations,none', [])  # Translations generated by the model
                matched_toxicity_list = data.get('matched_toxicity_list,none', []) 

                DATA_MODELS[modelname] = {  
                                            # metrics
                                            'comet-kiwi-etox': cometkiwi_etox,
                                            'comet-kiwi-mutox': cometkiwi_mutox,
                                            # text
                                            'sources':sources, 'translations': translations, 
                                            # toxicity
                                            'matched_toxicity_list': matched_toxicity_list,
                                            'etox':etox,
                                            'mutox':mutox,
                                            'n_sentences':n_sentences
                                        }

        # Tabs
        tab1, tab2, tab3 = st.tabs([
            "Corpus-Level Metrics", 
            "Toxic Segments",
            "Interactive Table"
        ])
        
        with tab1:
            
            if DATA_MODELS:

                # List of available metrics
                selected_metrics = ['etox%', 'mutox%', 'etox', 'mutox', 'comet-kiwi-etox', 'comet-kiwi-mutox']

                # Precompute the best metrics
                best_metrics = {
                    "comet-kiwi-etox": max(data_model['comet-kiwi-etox'] for data_model in DATA_MODELS.values()),
                    "comet-kiwi-mutox": max(data_model['comet-kiwi-mutox'] for data_model in DATA_MODELS.values()),
                    "etox": min(data_model['etox'] for data_model in DATA_MODELS.values()),
                    "mutox": min(data_model['mutox'] for data_model in DATA_MODELS.values()),
                }

                # Helper function to calculate delta and decide display logic
                def display_metric(column, name, value, best_value, inverse=False):
                    if value == INVALID_LOW or value == INVALID_HIGH or isinstance(value, str):
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

                    column.metric(name, round(value, 4), delta=delta_value, delta_color=delta_color)

                st.divider()
                # Loop through each model and display the selected metrics
                for modelname, data_model in DATA_MODELS.items():
                    st.markdown(f'###### **{modelname}**')

                    # show toxic nouns found
                    unique_toxic_words = set( [ i[0] for i in data_model['matched_toxicity_list'] if len(i) > 0] )
                    toxic_found = ""
                    for i in unique_toxic_words: toxic_found += f'*{i}*, '
                    if len(unique_toxic_words) > 0: st.markdown(f'**Found ETOX:** { toxic_found[:-2] }.' )

                    cols = st.columns(max(len(selected_metrics), 1))
                    
                    # Conditional display of selected metrics
                    for idx, metric in enumerate(selected_metrics):
                        if metric == 'comet-kiwi-etox':
                            display_metric(cols[idx], "COMET-KIWI-ETOX", data_model['comet-kiwi-etox'], best_metrics['comet-kiwi-etox'])
                        elif metric == 'comet-kiwi-mutox':
                            display_metric(cols[idx], "COMET-KIWI-MUTOX", data_model['comet-kiwi-mutox'], best_metrics['comet-kiwi-mutox'])
                        elif metric == 'etox%':
                            display_metric(cols[idx], "ETOX%", data_model['etox']/data_model['n_sentences'], best_metrics['etox']/data_model['n_sentences'], inverse=True)
                        elif metric == 'mutox%':
                            display_metric(cols[idx], "MUTOX%", data_model['mutox']/data_model['n_sentences'], best_metrics['mutox']/data_model['n_sentences'], inverse=True)
                        elif metric == 'etox':
                            display_metric(cols[idx], "ETOX", data_model['etox'], best_metrics['etox'], inverse=True)
                        elif metric == 'mutox':
                            display_metric(cols[idx], "MUTOX", data_model['mutox'], best_metrics['mutox'], inverse=True)
                    st.divider()

            else:
                st.warning("Corpus-Level Metrics require data from at least one model. Please select a model to proceed.")

        with tab2:
            st.subheader("Toxic segments")
            
            if DATA_MODELS:
                
                col_model, col_noun, col_index = st.columns(3)

                with col_model:
                    selected_modelname = st.selectbox(label='Select model to analyze',options=list(DATA_MODELS.keys()))
                data_model = DATA_MODELS[selected_modelname]

                unique_toxic_words = set( [ i[0] for i in data_model['matched_toxicity_list'] if len(i) > 0 ] )

                if len(unique_toxic_words) > 0:


                    with col_noun:
                        select_noun = st.selectbox(label='Select noun',options=unique_toxic_words)

                    data_model_copy = data_model.copy()
                    indices = [i for i, v in enumerate(data_model_copy['matched_toxicity_list']) if v == [select_noun]]
                    data_model_copy['sources'] = [v for i, v in enumerate(data_model_copy['sources']) if i in indices]
                    data_model_copy['translations'] = [v for i, v in enumerate(data_model_copy['translations']) if i in indices]

                    with col_index:
                        segment_index = st.number_input(
                            "Select Segment Index", 
                            min_value=0, 
                            max_value=len(data_model_copy['sources']) - 1, 
                            value=0, 
                            step=1
                        )
                    
                    
                    st.write(f"**Source Sentence:** {data_model_copy['sources'][segment_index]}")

                    if len(data_model['translations']) > 0:
                        st.write(f"**Translation:** {data_model_copy['translations'][segment_index]}")
                    else:
                        st.markdown('Translations are not available')

            else:
                st.warning("No data available for detailed segment view.")

        with tab3:

            st.subheader("Interactive Table")
            
            if DATA_MODELS:
                all_segment_data = []
                
                # Collect all data into a single DataFrame
                for modelname, data_model in DATA_MODELS.items():
                    num_segments = len(data_model['sources'])
                    for i in range(num_segments):
                        all_segment_data.append({
                            'Model': modelname,
                            'Source': get_string( data_model['sources'], i),
                            'Translation': get_string( data_model['translations'], i),
                            'Toxic noun': get_string(data_model['matched_toxicity_list'], i),
                        })
                
                segment_df = pd.DataFrame(all_segment_data)
                st.dataframe(segment_df)

            else:
                st.warning("No data available for interactive table.")
    else:
        st.error(f"File not found: {DATA_PATH_csv}. Please ensure the file exists.")

if __name__ == "__main__":
    main()