import sys
import copy
import streamlit as st
from streamlit_folium import folium_static
import get_device_locations as gdl
import get_device_categories  as gdc
import folium
from folium import plugins
import plotly.express as px
import pandas as pd
from onc.onc import ONC
import textwrap
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import datetime
from st_aggrid import AgGrid

st.set_page_config(page_title="Ocean Data Viewer", page_icon="🌊", layout="wide")


def app():

    st.markdown(f'<h1 style="color: orange;border-radius:50%;" >Ocean Data Viewer</h1>',unsafe_allow_html=True)

    st.markdown(f"<a style='color: orange;border-radius:50%;' >A prototype for displaying oceanographic instrument deployment sites and data using Ocean Networks Canada's api services.</a>",unsafe_allow_html=True)

    st.markdown(f'''<a style="color: orange;border-radius:50%;" >Usage: Enter your api token and select a device category name below. Time range can be set from the drop-down menu on left side of this page. The default is all.  
            Click on the pop-ups on the map to see near realtime data from each device.</a>''',unsafe_allow_html=True)

    def version_info():
        #Rule: Version: <Major>.<Minor>.<Patch/Upgrade>
        version = '0.0.0'
        st.markdown(
            f'''<a style="color:orange;font-size:12px;border-radius:0%;">Version: v{version}</a>''',
            unsafe_allow_html=True)

    version_info() 

    user_token = st.text_input ('Enter your api token:', '', type='password')
    user_input_anchor = st.columns ([1,4,5])
    map_anchor = st.columns ([2,1])

    token=user_token
    if user_token:
        onc = ONC (token)  

        deviceCat = gdc.get_device_categories(token)
        deviceCat = deviceCat[['deviceCategoryCode', 'deviceCategoryName']].append (
                    pd.DataFrame ({"deviceCategoryCode": [], "deviceCategoryName":[]}),
                    ignore_index=True).shift (1).fillna ("Select Device Category Name")

        deviceCategoryCode = deviceCat['deviceCategoryCode'].tolist ()

        deviceCategoryName = deviceCat['deviceCategoryName'].tolist ()

        class PutOnMap:
            # for parsing input
            def __init__(self, metadata):
                for key, value in metadata.items ():
                    if key == 'location': self.location = value,
                    if key == 'tiles': self.tiles = value,
                    if key == 'width': self.width = value,
                    if key == 'height': self.height = value,
                    if key == 'zoom_start': self.zoom_start = value

        dictionary = {'width': '100%', 'height': '100%', 'zoom_start': 150, 'location': [48.0, -125.250],
                        'tiles': "Stamen Terrain"}

        def plot_map(data, html_popup):
            try:
                df_tooltips = copy.deepcopy (data[['locationName', 'depth', 'deployments']])

                df_tooltips = df_tooltips.rename (
                    columns={"locationName": "Location Name: ", "depth": ", Water Depth (m): ",
                                "deployments": ", # of Deployments: "})
                df_tooltips[", Water Depth (m): "] = df_tooltips[", Water Depth (m): "].round (decimals=0)

                width, height = 1500, 600
                fig = folium.Figure (width=width, height=height)
                # use class putOnMap
                s = PutOnMap (dictionary)

                m = folium.Map (location=s.location[0], tiles=s.tiles[0],
                                width=s.width[0], height=s.height[0], zoom_start=s.zoom_start)
                folium.LatLngPopup ().add_to (m)
                folium.LayerControl ().add_to (m)

                k = 0
                for lon, lat in zip (data["lon"], data["lat"]):
                    test = folium.Html (html_popup, script=True)
                    iframe = folium.IFrame (html=test.render (), width=600, height=400)
                    #  put stuff on map
                    folium.Marker (
                        location=[lat, lon],  
                        popup=folium.Popup (iframe.render (), max_width=600, sticky=True),
                        tooltip=folium.Tooltip (df_tooltips.iloc[k, :].to_string ()),
                        icon=folium.Icon (color="blue", icon="glyphicon glyphicon-stats")  
                    ).add_to (m)
                    k += 1
                fig.add_child (m)
                return fig, m
            except KeyError:
                return False
                pass

        def plot_map_without_popups(data, wera_html):

            try:
                df_tooltips = copy.deepcopy (data[['locationName', 'depth', 'deployments']])

                df_tooltips = df_tooltips.rename (
                    columns={"locationName": "Location Name: ", "depth": ", Water Depth (m): ",
                                "deployments": ", # of Deployments: "})
                df_tooltips[", Water Depth (m): "] = df_tooltips[", Water Depth (m): "].round (decimals=0)

                width, height = 2400, 600
                fig = folium.Figure (width=width, height=height)
                # use class putOnMap
                s = PutOnMap (dictionary)

                m = folium.Map (location=s.location[0], tiles=None,
                                width=s.width[0], height=s.height[0], zoom_start=s.zoom_start)        
                # add optional layers
                folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                                attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community", name='World Imagery').add_to(m) 
                folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}', 
                                attr='Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ, and Esri',
                                    name='Ocean Basemap').add_to(m)                
                folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}', 
                                attr="Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC", name='Nat Geo Map').add_to(m)
                folium.TileLayer('openstreetmap').add_to(m)
                folium.TileLayer('cartodbdark_matter').add_to(m)
                folium.TileLayer('stamentoner').add_to(m)  

                folium.LatLngPopup ().add_to (m)
                folium.LayerControl ().add_to (m) 
                mini_map = plugins.MiniMap(toggle_display=True)
                m.add_child(mini_map)


                k = 0
                for lon, lat in zip (data["lon"], data["lat"]):
                    test = folium.Html (wera_html, script=True)
                    iframe = folium.IFrame (html=test, width=600, height=400)
                    #  put stuff on map
                    folium.Marker (
                        location=[lat, lon],  
                        popup=folium.Popup (iframe.render (), max_width=600, sticky=True),
                        tooltip=folium.Tooltip (df_tooltips.iloc[k, :].to_string ()), 
                        icon=folium.Icon (color="blue", icon="glyphicon glyphicon-stats")
                    ).add_to (m)
                    k += 1
                fig.add_child (m)
                return fig, m
            except KeyError:
                return False
                

        # Let user select a device category names, and use the device category codes to query the database
        select_device_type = user_input_anchor[0].selectbox (
            label='',
            options=deviceCategoryName)
        select_device_type_name = select_device_type
        deviceCategoryIndex = deviceCategoryName.index (select_device_type)
        select_device_type = deviceCategoryCode[deviceCategoryIndex]

        if select_device_type != "Select Device Category Name":
            select_start_date = st.sidebar.date_input (
                'Select start date', datetime.date (2001, 1, 1)
            )

            select_end_date = st.sidebar.date_input (
                'Select end date', datetime.date.today ()
            )

            if select_end_date is not datetime.date.today ():

                # ------------------------------------------------------
                # Set time spans
                dateFrom = select_start_date
                dateTo = select_end_date

        # get index of device category name
                parameters = {"devicelist": [select_device_type],
                                "dateFrom": dateFrom,
                                "dateTo": dateTo,
                                "minLat": 0.0,
                                "minLon": -180,
                                "maxLat": 90.0,
                                "maxLon": 180,
                                "title": 'Historical'

                                }

                df = gdl.get_device_locations (token, parameters)
                if len (df) == 0:
                    # update parameters for key devicelist when a user selects deviceCategory that does not have deployment history.
                    st.write (
                        f'{select_device_type} has no deployment history to show. Showing you a default deviceCategory (CTD).')
                    select_device_type = 'CTD'
                    parameters |= {"devicelist": [select_device_type]}
                    df = gdl.get_device_locations (token, parameters)

                def make_clickable(url):
                    return '<a href="{}" target="_blank">Data Download Link</a>'.format (url)

                df_show = copy.deepcopy (df)
                try:
                    df_show = df_show.drop (columns=["bbox", "hasPropertyData", "dataSearchURL"], axis=1)
                except KeyError:
                    pass

                try:
                    px_fig = px.bar (df, x="locationName", y="deployments", color="depth", width=2200, height=600)
                    px_fig.update_xaxes (type='category')
                    for data in px_fig.data:
                        data["width"] = 0.15
                    expander = st.expander (f"{select_device_type_name} Deployments Details ({dateFrom} - {dateTo})")
                    expander.subheader (f"{select_device_type_name} Deployment Histograms")
                    tot_number = df["deployments"].sum ()
                    expander.write (f" Time period: {dateFrom} - {dateTo}, Total number of deployments: {tot_number}")

                    expander.plotly_chart (px_fig, use_container_width=True)
                except ValueError:
                    st.write (
                        f'No deployment details to show for deviceCategory: {select_device_type_name} for the time period {dateFrom} - {dateTo}')
                    pass

                #  --------------------get data for popup plots---------------
                def get_by_location(**kwargs):
                    _deviceCategoryCode = kwargs.get ("deviceCategoryCode")
                    _locationCode = kwargs.get ("locationCode")
                    _rowLimit = kwargs.get ("rowLimit")
                    _dateFrom = kwargs.get ("dateFrom")
                    _dateTo = kwargs.get ("dateTo")
                    scalars = onc.getDirectByLocation ({"locationCode": _locationCode,
                                                        "deviceCategoryCode": _deviceCategoryCode,
                                                        "dateFrom": _dateFrom,
                                                        "dateTo": _dateTo}, allPages=True)

                    if scalars and scalars['sensorData']:
                        # we're interested in only sensor data from the api response
                        return pd.json_normalize (scalars['sensorData'])
                    else:
                        pass
                        # TypeError  #: 'NoneType' object is not subscriptable
                        # st.write (
                        #     "No data parsed for locationCode {} and deviceCategoryCode {}\
                        #         for the given time period ".format (
                        #         _locationCode, _deviceCategoryCode)
                        # )
                        return None

                @st.cache
                def get_data_for_popup_plot():
                    """"
                    set search parameters and query parsed data.
                    The dates will be fixed between now and 5min ago max to get data quicker;
                    others will be user selectable
                    """

                    _deviceCategoryCode = select_device_type
                    _now = onc.formatUtc (str (pd.Timestamp (datetime.datetime.now ())))
                    _one_hour_ago = onc.formatUtc (
                        str (pd.Timestamp (datetime.datetime.now () - datetime.timedelta (minutes=5))))

                    _dateFrom = _one_hour_ago
                    _dateTo = _now
                    try:
                        for location_code in df['locationCode']:
                            try:
                                _locationCode = location_code
                                params = {"locationCode": _locationCode, "deviceCategoryCode": _deviceCategoryCode,
                                            "dateFrom": _dateFrom,
                                            "dateTo": _dateTo}
                                df_pops = get_by_location (**params)
                                if df_pops is not None:
                                    return df_pops
                                else:
                                    pass
                                    # st.write (
                                    #         "No data parsed for locationCode {} and deviceCategoryCode {}\
                                    #          for the given time period ".format (
                                    #       _locationCode, _deviceCategoryCode)
                                    #      )   
                            except TypeError:

                                pass
                    except KeyError:
                        pass

                        

                df_popup = get_data_for_popup_plot ()
                # break long yaxis label strings ( longer than 25 chars)
                def wrap(string, max_width):
                    return '<br>'.join (textwrap.wrap (string, max_width))

                def figs_show(figs):
                    titles = [fgs.name for fgs in figs['data']]
                    # trick plotly by adding blank str
                    titles.insert (1, "")

                    new_titles = [[i, wrap (title, 25)] for i, title in zip (range (len (titles)), titles) if
                                    len (title) > 25]
                    for new_title in new_titles:
                        titles[new_title[0]] = new_title[1]

                    # Now update the y axis labels with sensor names, and display figures
                    for i in range (0, len (titles)):
                        if i == 0:
                            figs['layout']["yaxis"].title = titles[i]
                        elif i == 1:
                            pass
                        else:
                            figs['layout'][f"yaxis{i}"].title = titles[i]

                    figs.update_yaxes (side='top')
                    figs.update_layout (showlegend=False)
                    return figs

                if df_popup is not None:
                    fig = make_subplots (rows=
                                            len (df_popup), cols=1, shared_xaxes=False,
                                            vertical_spacing=0.04)

                    def get_pop_ups_plot(df_p):
                        N = len (df_p)
                        try:
                            for i in range (len (df_p)):
                                data_name = '{}({})'.format (df_p["sensorName"][i], df_p["unitOfMeasure"][i])
                                df_to_plot = pd.DataFrame (
                                    {"time": df_p['data.sampleTimes'][i], data_name: df_p['data.values'][i]})

                                fig.append_trace (go.Scatter (
                                    x=df_to_plot["time"],
                                    y=df_to_plot[data_name], name=data_name
                                ), row=i + 1, col=1)
                            fig.update_layout (height=300 * N,
                                                width=580,
                                                legend=dict (
                                                    yanchor="middle",
                                                    xanchor="right",
                                                    x=1.2,
                                                    y=0.5),
                                                hoverlabel=dict (
                                                    bgcolor="white",
                                                    font_size=14,
                                                    font_family="Rockwell"),
                                                hovermode='x unified',
                                                paper_bgcolor="LightSteelBlue"
                                                )
                            fg = figs_show (fig)

                            return fig

                        except IndexError:
                            print ("No parsed data to plot.")
                            pass

                    def get_pop_ups():
                        return get_pop_ups_plot (df_popup)

                    def map_callback():

                        html = get_pop_ups ()
                        # --------------------
                        # convert it to JSON
                        fig_json = html.to_json ()

                        # a simple HTML template with proper heading to display charts in iframe
                        # Source: https://stackoverflow.com/questions/36262748/python-save-plotly-plot-to-local-file-and-insert-into-html
                        template = """<html>
                            <head>
                                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                            </head>
                            <body>
                                <div id='divPlotly'></div>
                                <script>
                                    var plotly_data = {}
                                    Plotly.react('divPlotly', plotly_data.data, plotly_data.layout);
                                </script>
                            </body>
                        
                            </html>"""

                        html = template.format (fig_json)
                        # ------------------------------------------------------------------------
                        try:
                            fig, m = plot_map_without_popups (df, html)
                        except TypeError:
                            # if deviceCategory has no all the common deployment info, just plot the bare map
                            map_dict = {'width': '100%', 'height': '100%', 'zoom_start': 12, 'lat': 48.0, 'lon': -125.250,
                                        'tiles': None}
                            m = folium.Map (**map_dict)
                            pass

                        return m

                    m = map_callback ()           

                else:
                    # replace this with more elegant solution later
                    wera_dash_html = '''      
                                    <!DOCTYPE html>
                                    <html>

                                    <head>
                                    <meta charset="UTF-8">
                                    <title>Wera Tofino</title>
                                    <script src="http://onc.danycabrera.com/engines/plotly.min.js"></script>
                                    <link rel="stylesheet" href="https://s3.us-west-2.amazonaws.com/onc.zesys.ca/oncdw.1.css" />
                                    <script src="https://s3.us-west-2.amazonaws.com/onc.zesys.ca/oncdw.1.min.js" id="oncdw" data-token=""></script>
                                    <style>
                                        h1{position:fixed;top:0;left:0;right:0;width:180px;height:36px;box-sizing:border-box;color:#b0c4de;margin:0;padding:8px 6px;font-size:14px;z-index:10000000;border-bottom:1px solid #b0c4de;border-right:1px solid #12598a;background:transparent;box-shadow:0 3px 1px rgba(0,0,0,0.2)}.sidenav{height:100%;width:240px;position:fixed;z-index:1;top:28px;left:0;background-color:#b0c4de;overflow-x:hidden}.sidenav ul,.sidenav li{padding:0;margin:0;list-style-type:none}.sidenav ul.nav{padding:10px 2px}.sidenav ul.nav ul{margin-bottom:16px}.sidenav a{display:block;text-decoration:none;border:1px solid #666;margin-bottom:2px}.sidenav a:hover>span{background:#fffddf}.sidenav .device,.sidenav .sensor{position:relative;display:block;background-color:transparent;font-size:12px;line-height:16px;padding:6px 14px}.sidenav .device span,.sidenav .sensor span{position:absolute;left:0;top:0;bottom:0;padding:6px 8px;min-width:42px;text-align:center;color:#FFF}.sidenav .device span{background-color:#094e4b}.sidenav .sensor span{background-color:#804015}.sidenav .device{color:#03534f;border-color:#b0c4de;padding-left:66px}.sidenav .sensor{color:#92430f;border-color:#b3500e;padding-left:66px}.main{position:relative;margin-left:240px;padding:10px 10px 10px 10px}body{background:#b0c4de;font-family:-apple-system,'Helvetica Neue','Helvetica','Arial','Lucida Grande',sans-serif;-webkit-font-smoothing:antialiased}.clear{clear:both}.widgetWrap .oncWidget{width:100%}.widgetWrap .statusMsg{margin-top:15px}.widgetWrap{padding:10px 16px;margin:15px 0 25px;background:transparent;color:#b0c4de;box-sizing:border-box;font-size:12px;box-shadow:0 .175em .5em rgba(2,8,20,.2),0 .085em .175em rgba(2,8,20,.16);border-radius:4px}.widgetWrap .site,.widgetWrap .device,.widgetWrap .sensor{position:relative;display:inline-block;color:#fff;font-size:.85714286rem;border-radius:.28571429rem;padding:6px 14px;margin-right:10px}.widgetWrap .device span,.widgetWrap .sensor span{position:absolute;left:0;top:0;bottom:0;padding:6px 8px;border-top-left-radius:.28571429rem;border-bottom-left-radius:.28571429rem}.widgetWrap .device span{background-color:transparent}.widgetWrap .sensor span{background-color:#b0c4de}.widgetWrap .site{background-color:#b0c4de;border-color:transparent}.widgetWrap .device{background-color:transparent;border-color:transparent;padding-left:66px;margin-bottom:10px}.widgetWrap .sensor{background-color:transparent;border-color:transparent;font-weight:bold;padding-left:66px}
                                    </style>
                                    </head>

                                    <body>
                                    <!-- Sidebar navigation  
                                    <h1>WERA Tofino</h1>
                                            -->
                                    <div class="sidenav">
                                        <ul class="nav"</ul>
                                    <a href="#w_77"><span class="device"><span>22962</span> WERA Tofino Radar</span></a>
                                            <ul>
                                                <li><a href="#w_166"><span class="sensor"><span></span> Radial Velocity</span></a>
                                                </li>
                                                <li><a href="#w_167"><span class="sensor"><span></span> Significant wave height</span></a>
                                                </li>
                                                <li><a href="#w_168"><span class="sensor"><span></span> Tsunami Probability</span></a>
                                                </li>
                                            </ul>
                                    </div>
                                    <!-- Plot widgets -->
                                    <!-- Plot widgets -->
                                    <div class="main">
                                        <div id="w_166">
                                            <figure class="oncWidget" data-widget="image" data-source="dataPreview" url="https://data.oceannetworks.ca/DataPreviewService?operation=5&searchTreeNodeId=521&deviceCategoryId=65&timeConfigId=2&dataProductFormatId=245&plotNumber=1" options="theme: gallery" </figure>
                                        </div>
                                        <div class="clear" id="w_167">
                                            <figure class="oncWidget" data-widget="image" data-source="dataPreview" url="https://data.oceannetworks.ca/DataPreviewService?operation=5&searchTreeNodeId=521&deviceCategoryId=65&timeConfigId=2&dataProductFormatId=246&plotNumber=1" options="theme: gallery" </figure>
                                        </div>
                                        <div class="clear" id="w_168">
                                            <figure class="oncWidget" data-widget="image" data-source="dataPreview" url="https://data.oceannetworks.ca/DataPreviewService?operation=5&searchTreeNodeId=521&deviceCategoryId=65&timeConfigId=2&dataProductFormatId=247&plotNumber=1" options="theme: gallery" </figure>
                                        </div>
                                    </div>
                                    </body>
                                    </html>
                                    '''

                    fig, m = plot_map (df, wera_dash_html)

                # Wave Rider
                folium.Marker (
                    location=[48.9, -126.05],
                    popup='Do we have data here?',
                    tooltip=folium.Tooltip ('Wave Rider'),
                    icon=folium.Icon (color="red", icon="glyphicon glyphicon-tower")  
                ).add_to (m)

                # Tofino Airport
                folium.Marker (
                    location=[49.0750, -125.7654],
                    popup='Tofino Airport',
                    icon=folium.Icon (color="purple", icon="glyphicon glyphicon-plane")  
                ).add_to (m)

                m.fit_bounds (m.get_bounds ())

                with map_anchor[0]:
                    st.subheader (f"{select_device_type_name} Deployment Locations")
                    st.write (f" Time period: {dateFrom} - {dateTo}, Total number of deployments: {tot_number}")
                    folium_static (m, height=700, width=1500)

                with expander:  
                    st.subheader (f"{select_device_type_name} Deployment Details")
                    AgGrid (df_show)
                    st.subheader (f"Total number of deployments: {tot_number}")

    else:
        st.warning(f''' Please enter your api token to continue.
            ''')

    column1, column2, column3 = st.columns (3)

    user_wishlist = column1.text_input (label='your feedback:')
    user_email = column2.text_input (label='email(optional):')
    submit_feedback = column1.button (label='submit feedback now')
    if submit_feedback:
        with open ('assets/txt/user_wishlist.txt', 'a') as wishlistfile:
            wishlistfile.write (f'{datetime.datetime.now ()}\t:{user_wishlist}\t{user_email}\n')
        st.write ('Thanks for your feedback!')
    st.markdown('Docker image:')
    st.code('docker pull zesys0/oceanviewstreamlitapp')

if __name__ == '__main__':
    app()       
