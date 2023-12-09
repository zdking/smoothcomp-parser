from datetime import datetime
import requests
import time
import pandas as pd
import streamlit as st
from pytz import timezone


def _urlToDataFrame(url):
    dataFrame = pd.json_normalize(
        requests.get(url).json(),
        record_path="seats",
        meta=["mat_match_nr", "estimated_start"],
    )
    dataFrame["mat_match_nr"] = dataFrame["mat_match_nr"].map(lambda x: x[:1])
    return dataFrame


def _matToDataFrame(url):
    return (
        _urlToDataFrame(url)
        .query('club == "Gracie Brandon"')
        .rename(
            columns={
                "name": "Fighter Name",
                "estimated_start": "Estimated Start Time",
                "mat_match_nr": "Mat",
            }
        )
        .loc[:, ["Estimated Start Time", "Mat", "Fighter Name"]]
    )


def _matsToDataFrame(matIds):
    return (
        pd.concat(
            (
                [
                    _matToDataFrame(
                        f"https://newbreedbjj.smoothcomp.com/en/event/12651/schedule/new/mat/{matId}/matches.json?upcoming=true"
                    )
                    for matId in matIds
                ]
            )
        )
        .sort_values(
            by=["Estimated Start Time"],
            key=lambda col: pd.to_datetime("20231209 " + col, format="%Y%m%d %I:%M %p"),
            ascending=True,
        )
        .reset_index(drop=True)
    )


def _displaySchedule(layout):
    with layout["row2"], st.status(layout["loadingText"]) as status:
        schedule = _matsToDataFrame(matIds)
        layout["row3"].table(schedule)
        layout["row1"].write(
            "Last Refresh: {lastRefresh}".format(
                lastRefresh=datetime.now(timezone("EST")).strftime("%H:%M:%S")
            )
        )

        for seconds in range(10, 0, -1):
            status.update(label=f"Next Refresh: {seconds} second(s)", state="running")
            time.sleep(1)

        loadingText = "Refreshing Schedule..."


layout = {
    "row1": st.empty(),
    "row2": st.empty(),
    "row3": st.empty(),
    "loadingText": "Loading Schedule...",
}

while True:
    _displaySchedule(layout)
