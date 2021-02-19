This started from a divergent branch of the GraphingData repo. Unlike GraphingData, this needs the pyarrow module, which fails to install nicely on at least Windows 10 LTSB and Windows 7 Pro. If you have issues too, try using GraphingData instead. Supposedly there are new features and bugfixes in OriginDataView, but the original author (Bradley Nordin) did not enumerate them here and I have not personally sifted through the code as of yet. - PH


# StreamlitUI
Origin Graphing UI written with Streamlit

To install: 
Install pipenv (pip install pipenv) 
clone the repository
navigate inside repository folder 
run pipenv install

To start, select the Origin streams from the sidebar. This sidebar can be collapsed

Every interaction with a widget, but not the dropdowns, will rerun the whole script and 
stop the subscription execution.
Just click the start subscribing button to resubscribe.

You can click the plot legends to select which data is plotted.

The date range picker only works for the current day, for now

When in doubt, refresh page
