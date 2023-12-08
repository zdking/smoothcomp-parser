import requests
import pandas as pd
import streamlit as st




def _matToDataFrame(url):
    df = pd.json_normalize(requests.get(url).json(), record_path='seats', meta=["mat_match_nr","estimated_start"])
    df['mat_match_nr'] = df['mat_match_nr'].apply(lambda x: x[:1])
    df = df.query('club == "Gracie Brandon"').rename(columns={'name': 'Fighter Name', 'estimated_start': 'Estimated Start Time', 'mat_match_nr' : 'Mat'})
    return df[['Estimated Start Time', 'Mat', 'Fighter Name']]

mat_ids = ['74036','74037','74038','74039','74040','74041']
schedule = pd.concat(([_matToDataFrame('https://newbreedbjj.smoothcomp.com/en/event/12651/schedule/new/mat/{mat_id}/matches.json?upcoming=true'.format(mat_id=mat_id)) for mat_id in mat_ids]))
st.markdown("<script> setTimeout(function(){ window.location.reload(); }, 10000);</script>", unsafe_allow_html=True)
st.table(schedule.sort_values(by=['Estimated Start Time'],key=lambda col: pd.to_datetime('20231209 ' + schedule['Estimated Start Time'], format='%Y%m%d %I:%M %p'), ascending=True))
