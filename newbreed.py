from datetime import datetime
import requests
import time
import pandas as pd
import streamlit as st
import numpy as np
from pytz import timezone


def _urlToDataFrame(url):
    dataFrame = pd.json_normalize(
        requests.get(url).json(),
        record_path="seats",
        meta=["mat_match_nr", "estimated_start"],
    )
    if dataFrame.empty == False:
        dataFrame["mat_match_nr"] = dataFrame["mat_match_nr"].map(lambda x: x[:1])

    return dataFrame


def _matToDataFrame(url):
    dataFrame = _urlToDataFrame(url)
    if dataFrame.empty == False:
        dataFrame = (
            dataFrame.query('club == "Gracie Brandon"')
            .rename(
                columns={
                    "name": "Fighter Name",
                    "estimated_start": "Estimated Start Time",
                    "mat_match_nr": "Mat",
                }
            )
            .loc[:, ["Estimated Start Time", "Mat", "Fighter Name"]]
        )

    return dataFrame


def _matsToDataFrame(matIds):
    dataFrame = pd.concat(
        (
            [
                _matToDataFrame(
                    f"https://newbreedbjj.smoothcomp.com/en/event/12651/schedule/new/mat/{matId}/matches.json?upcoming=true"
                )
                for matId in matIds
            ]
        )
    )
    if dataFrame.empty == False:
        dataFrame = dataFrame.sort_values(
            by=["Estimated Start Time"],
            key=lambda col: pd.to_datetime("20231209 " + col, format="%Y%m%d %I:%M %p"),
            ascending=True,
        ).reset_index(drop=True)

    return dataFrame


def _displaySchedule(layout):
    with layout["row2"], st.status(layout["loadingText"]) as status:
        status.update(label=layout["loadingText"], state="running")
        layout["row3"].table(_matsToDataFrame(matIds))
        layout["row1"].write(
            "Last Refresh: {lastRefresh}".format(
                lastRefresh=datetime.now(timezone("EST")).strftime("%H:%M:%S")
            )
        )

        for seconds in range(10, 0, -1):
            status.update(label=f"Next Refresh: {seconds} second(s)", state="running")
            time.sleep(1)

        layout["loadingText"] = "Refreshing Schedule..."


matIds = ["74036", "74037", "74038", "74039", "74040", "74041"]
layout = {
    "row1": st.empty(),
    "row2": st.empty(),
    "row3": st.empty(),
    "loadingText": "Loading Schedule...",
}

while True:
    _displaySchedule(layout)
