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
        meta=["mat_match_nr", "estimated_start", "state", "wonBy", "group"],
    )

    if dataFrame.empty == False:
        dataFrame = dataFrame.astype({"isWinner": str})
        dataFrame["mat_match_nr"] = dataFrame["mat_match_nr"].map(lambda x: x[:1])
        dataFrame["isWinner"] = dataFrame["isWinner"].map(
            lambda x: "WON" if x == "True" else "LOST"
        )

    return dataFrame


def _matToDataFrame(url):
    dataFrame = _urlToDataFrame(url)
    if dataFrame.empty == False:
        dataFrame = dataFrame.query('club == "Gracie Brandon"').rename(
            columns={
                "name": "Fighter Name",
                "estimated_start": "Estimated Start Time",
                "mat_match_nr": "Mat",
                "state": "State",
                "isWinner": "Win/Loss",
                "wonBy": "Win/Loss by",
                "group": "Bracket",
            }
        )

    return dataFrame


def _matsToDataFrame(matIds):
    dataFrame = pd.concat(
        (
            [
                _matToDataFrame(
                    f"https://newbreedbjj.smoothcomp.com/en/event/13776/schedule/new/mat/{matId}/matches.json"
                    # f"https://newbreedbjj.smoothcomp.com/en/event/12651/schedule/new/mat/{matId}/matches.json"
                )
                for matId in matIds
            ]
        )
    )
    if dataFrame.empty == False:
        dataFrame = dataFrame.sort_values(
            by=["Estimated Start Time"],
            key=lambda col: pd.to_datetime("20240210 " + col, format="%Y%m%d %I:%M %p"),
            ascending=True,
        ).reset_index(drop=True)

    return dataFrame


def _displaySchedule(layout):
    with layout["row2"], st.status(layout["loadingText"]) as status:
        status.update(label=layout["loadingText"], state="running")
        allData = _matsToDataFrame(matIds)
        with layout["row3"] as row3:
            tab1, tab2 = st.tabs(["Upcoming", "Completed"])
            with tab1:
                st.table(
                    allData.query('State != "finished"').loc[
                        :,
                        ["Estimated Start Time", "Mat", "Fighter Name", "Bracket"],
                    ]
                )
            with tab2:
                st.table(
                    allData.query('State == "finished"')
                    .rename(
                        columns={
                            "Estimated Start Time": "Match Time",
                        }
                    )
                    .loc[
                        :,
                        [
                            "Match Time",
                            "Mat",
                            "Fighter Name",
                            "Bracket",
                            "Win/Loss",
                            "Win/Loss by",
                        ],
                    ]
                )

        layout["row1"].write(
            "Last Refresh: {lastRefresh}".format(
                lastRefresh=datetime.now(timezone("EST")).strftime("%H:%M:%S")
            )
        )

        for seconds in range(10, 0, -1):
            status.update(label=f"Next Refresh: {seconds} second(s)", state="running")
            time.sleep(1)

        layout["loadingText"] = "Refreshing Schedule..."


matIds = ["80427", "80428", "80429", "80430", "80431", "93236"]
# matIds = ["74036", "74037", "74038", "74039", "74040", "74041"]
layout = {
    "row1": st.empty(),
    "row2": st.empty(),
    "row3": st.empty(),
    "loadingText": "Loading Schedule...",
}

while True:
    _displaySchedule(layout)
