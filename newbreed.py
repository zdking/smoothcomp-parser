from datetime import datetime
import urllib.parse
import requests
import time
import pandas as pd
import streamlit as st
import numpy as np
import re
import pytz
import json
import urllib


def _urlToDataFrame(url):
    dataFrame = pd.json_normalize(
        requests.get(url).json(),
        record_path="seats",
        meta=["mat_match_nr", "estimated_start", "state", "wonBy", "group"],
    )

    if dataFrame.empty == False:
        dataFrame = dataFrame.astype({"isWinner": str})
        dataFrame["mat_match_nr"] = dataFrame["mat_match_nr"].map(lambda x: x[:1])
        dataFrame["group"] = dataFrame["group"].map(
            lambda x: "Gi" if re.search("no-gi", x, re.IGNORECASE) is None else "No-Gi"
        )
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
                "group": "Match Type",
            }
        )

    return dataFrame


def _matsToDataFrame(matUrls):
    return pd.concat(([_matToDataFrame(matUrl) for matUrl in matUrls]))


def _displaySchedule(layout, matUrls):
    with layout["row0"] as row0:
        st.empty()
    with layout["row2"], st.status(layout["loadingText"]) as status:
        status.update(label=layout["loadingText"], state="running")
        allData = _matsToDataFrame(matUrls)
        with layout["row3"] as row3:
            upcomingTab, completedTab = st.tabs(["Upcoming", "Completed"])
            with upcomingTab:
                st.table(
                    allData.query('State != "finished"')
                    .sort_values(
                        by=["Estimated Start Time"],
                        key=lambda col: pd.to_datetime(
                            "20240525 " + col, format="%Y%m%d %I:%M %p"
                        ),
                        ascending=True,
                    )
                    .reset_index(drop=True)
                    .loc[
                        :,
                        ["Estimated Start Time", "Mat", "Fighter Name", "Match Type"],
                    ]
                )
            with completedTab:
                st.table(
                    allData.query('State == "finished"')
                    .sort_values(
                        by=["Estimated Start Time"],
                        key=lambda col: pd.to_datetime(
                            "20240525 " + col, format="%Y%m%d %I:%M %p"
                        ),
                        ascending=False,
                    )
                    .reset_index(drop=True)
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
                            "Match Type",
                            "Win/Loss",
                            "Win/Loss by",
                        ],
                    ]
                )

        with layout["row1"] as row1:
            st.write(
                "Last Refresh: {lastRefresh}".format(
                    lastRefresh=datetime.now(pytz.timezone("EST")).strftime("%H:%M:%S")
                )
            )

        for seconds in range(10, 0, -1):
            status.update(label=f"Next Refresh: {seconds} second(s)", state="running")
            time.sleep(1)

        layout["loadingText"] = "Refreshing Schedule..."

        return len(allData.query('State != "finished"')) == 0


def _getUrlsForEvent(eventPath: str):
    response = requests.get(
        urllib.parse.urljoin(urlBase, f"{eventPath}/schedule/new/matcategories.json")
    )
    if response.status_code == 200:
        matCategoryId = response.json()[0]["id"]
        matsUrl = urllib.parse.urljoin(
            urlBase, f"{eventPath}/schedule/new/mats.json/{matCategoryId}"
        )
        response = requests.get(matsUrl)

        _monitorEvent(
            [
                urllib.parse.urljoin(
                    urlBase,
                    f"{eventPath}/schedule/new/mat/{mat['id']}/matches.json",
                )
                for mat in response.json()
            ]
        )


def _monitorEvent(matUrls):
    finished = False
    while not finished:
        finished = _displaySchedule(layout, matUrls)


# could be used to show upcoming events, but is disabled for simplicity
# def _displayEvents(layout, eventsUrl):
#     response = requests.get(eventsUrl)
#     parsedData = bs(response.content, "html.parser")
#     data = parsedData.find("script", attrs={"type": "application/ld+json"})
#     with layout["row0"] as row0:
#         with st.container() as butts:
#             for item in json.loads(data.string)["itemListElement"]:
#                 parsedUrl = urlparse(item["url"])
#                 _getUrlsForEvent(parsedUrl.path)


urlBase = "https://newbreedbjj.smoothcomp.com"
newEventsUrl = urllib.parse.urljoin(urlBase, "/en/federation/65/events/upcoming")
pastEventsUrl = urllib.parse.urljoin(urlBase, "/en/federation/65/events/past")

layout = {
    "row0": st.empty(),
    "row1": st.empty(),
    "row2": st.empty(),
    "row3": st.empty(),
    "loadingText": "Loading Schedule...",
}

# used when showing upcoming events, but is disabled for simplicity
# _displayEvents(layout, newEventsUrl)
_getUrlsForEvent("https://newbreedbjj.smoothcomp.com/en/event/15678")
