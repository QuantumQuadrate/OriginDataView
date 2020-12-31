import streamlit as st
import time

myList = []
data = range(10)
for i in range(10):
    myList.append(st.empty())

for chart in myList:
    chart.line_chart(data)

time.sleep(3)

for chart in myList:
    chart.line_chart(range(100))