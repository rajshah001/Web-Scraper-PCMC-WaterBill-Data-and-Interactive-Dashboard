from os.path import dirname, join

import pandas as pd
import numpy as np
# For Pie Chart
from math import pi
from bokeh.io import show, output_file
from bokeh.palettes import Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum
# For DataTable
from bokeh.models import ColumnDataSource, RangeSlider, Button, CustomJS, NumberFormatter 
from bokeh.models.widgets import DataTable, TableColumn, Select, Tabs, Panel
# For Layouts
from bokeh.layouts import column, row, widgetbox, layout, gridplot
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.server.server import Server
# For Maps
from sklearn import preprocessing
from bokeh.tile_providers import get_provider, Vendors
import warnings
warnings.filterwarnings('ignore')
import math
from ast import literal_eval
# For Bar Chart
from bokeh.palettes import Spectral6
from bokeh.transform import factor_cmap


# Function to convert Lattitude and Longitude to Mercator Projection range.
def merc(Coords):
    Coordinates = literal_eval(Coords)
    lat = Coordinates[0]
    lon = Coordinates[1]
    
    r_major = 6378137.000
    x = r_major * math.radians(lon)
    scale = x/lon
    y = 180.0/math.pi * math.log(math.tan(math.pi/4.0 + 
        lat * (math.pi/180.0)/2.0)) * scale
    return (x, y)


# Creating a DataFrame to read the excel sheet data which is uncatogorized w.r.t. to regions.
# df = pd.read_excel('PCMC_WaterBill_Data1.xlsx')
df = pd.read_csv('PCMC_WaterBill_Data.csv', sep='|')

# Creating some list variables for sorting the data region-wise.
marathi_local = []
available_loc = []
not_available_loc = []

# Reading localities data from "marathi_localities_pune.txt" file which is in the current working directory.
with open('marathi_localities_pune.txt', 'r', encoding='utf-8') as f:
    for i in f:
        marathi_local.append(i.strip())

# Decalring a new DataFrame for the cleanzed data which is catogorized w.r.t. to regions.
main_df = pd.DataFrame()

counter = 0
for i in marathi_local:
    loc_df = df.loc[df['address'].str.contains(i,  na=False)]
    if loc_df.shape[0] > 50:
        main_df = pd.concat([loc_df, main_df])
        available_loc.append([i, loc_df.shape[0]])
        counter += loc_df.shape[0] 
    else:
        not_available_loc.append(i)
        
output_file('output.html')
print('starting fun')
##############################################################################################################

# Create the Bokeh Document Application
def modify_doc(doc):
    
    # Create the main plots
    def create_figure():
        current_loc_name = loc_name.value
        data = main_df.loc[main_df['address'].str.contains(current_loc_name,  na=False)]
        
        ######################################################################################################
        # Data Preparation for connection_type
        residential = (data.connection_type.values == 'Residential').sum()
        commercial = (data.connection_type.values == 'Commercial').sum()
        semi_government = (data.connection_type.values == ['semi government' or 'Semi government']).sum()
        public = (data.connection_type.values == 'Public').sum()
        corporation = (data.connection_type.values == 'Corporation').sum()
        x = {'Residential': residential,
             'Commercial' : commercial,
             'Semi Government' : semi_government,
             'Public' : public,
             'Corporation' : corporation}
        connection_type_data = pd.DataFrame({'connection_type': list(x.keys()), 'value': list(x.values())})

        connection_size_data = pd.DataFrame(data['connection_size'].value_counts()).rename(columns={'connection_size':'value'})
        connection_size_data.index.name = 'connection_size'

        # Data Preparation for location data
        map_data = data.dropna(subset=['location'])
        map_data.drop_duplicates(subset='consumer_id', keep="last", inplace=True)
        map_data['coords_x'] = map_data['location'].apply(lambda x: merc(x)[0])
        map_data['coords_y'] = map_data['location'].apply(lambda x: merc(x)[1])
        print(map_data['due_amount'].max())
        # Create x, where x the 'due_amount' column's values as floats
        x = map_data[['due_amount']].values.astype(float)
        # Create a minimum and maximum processor object
        min_max_scaler = preprocessing.MinMaxScaler()
        # Create an object to transform the data to fit minmax processor
        x_scaled = min_max_scaler.fit_transform(x)
        map_data['circle_size'] = x_scaled*100
        
        map_source = ColumnDataSource(data=dict(
                        x=list(map_data['coords_x']), 
                        y=list(map_data['coords_y']),
                        due_amount=list(map_data['due_amount']),
                        sizes=list(map_data['circle_size']),
                        consumer_id=list(map_data['consumer_id']),
                        consumer_name=list(map_data['consumer_name']),
                        billing_frequency=list(map_data['billing_frequency'])))

        ######################################################################################################
        # For DataTable of connection_type
        connection_type_source = ColumnDataSource(connection_type_data)

        columns = [TableColumn(field="connection_type", title="connection_type"),
                   TableColumn(field="value", title="value")]
        connection_type_data_table = DataTable(source=connection_type_source, columns=columns, width=250, height=300)
        
        # Pie Chart of connection_type
        connection_type_data['angle'] = connection_type_data['value']/connection_type_data['value'].sum()*2*pi
        connection_type_data['color'] = Category20c[len(connection_type_data)]

        connection_type_pie = figure(plot_height=350, title="Pie Chart", toolbar_location="right",
                   tools="hover, pan, wheel_zoom, box_zoom, reset", tooltips="@connection_type: @value", x_range=(-0.5, 1.0))
        connection_type_pie.wedge(x=0, y=1, radius=0.4,
                start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                line_color="white", fill_color='color', legend_field='connection_type', source=connection_type_data)
        #######################################################################################################
        # For DataTable of connection_size
        connection_size_source = ColumnDataSource(pd.DataFrame(connection_size_data))

        columns = [TableColumn(field="connection_size", title="connection_size"),
                   TableColumn(field="value", title="value")]
        connection_size_data_table = DataTable(source=connection_size_source, columns=columns, width=250, height=300)
        
        # Pie Chart of connection_size
        connection_size_data['angle'] = connection_size_data['value']/connection_size_data['value'].sum()*2*pi
        connection_size_data['color'] = Category20c[len(connection_size_data)]

        connection_size_pie = figure(plot_height=350, title="Pie Chart", toolbar_location="right",
                   tools="hover, pan, wheel_zoom, box_zoom, reset", tooltips="@connection_size: @value", x_range=(-0.5, 1.0))
        connection_size_pie.wedge(x=0, y=1, radius=0.4,
                start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                line_color="white", fill_color='color', legend_field='connection_size', source=connection_size_data)
        ########################################################################################################
        # Map Chart
        tooltips=[
            ("Consumer ID", "@consumer_id"),
            ("Consumer Name","@consumer_name"),
            ("Due Amount", "@due_amount"),
            ("Billing Frequency", "@billing_frequency")]
        map_chart = figure(x_axis_type="mercator", y_axis_type="mercator", tools="hover, pan, wheel_zoom, box_zoom, reset", tooltips=tooltips, width=250, height=300)
        map_chart.add_tile(get_provider(Vendors.CARTODBPOSITRON_RETINA))
        map_chart.circle(x = 'x',
                 y = 'y',
                 size = 'sizes',
                 source = map_source,
                 fill_alpha = 0.05)


        #######################################################################################################
        # For BarPlot of billing_frequency
        billing_freq_tags = list(dict(data['billing_frequency'].value_counts()).keys())
        billing_freq_data = list(dict(data['billing_frequency'].value_counts()).values())
        
        source = ColumnDataSource(data=dict(billing_freq_tags=billing_freq_tags, billing_freq_data=billing_freq_data))

        billing_frequency_bar = figure(x_range=billing_freq_tags, plot_height=250, toolbar_location=None, title="Billing Frequency of Connection holders")
        billing_frequency_bar.vbar(x='billing_freq_tags', top='billing_freq_data', width=0.9, source=source, legend_field="billing_freq_tags",
               line_color='white', fill_color=factor_cmap('billing_freq_tags', palette=Spectral6, factors=billing_freq_tags))

        billing_frequency_bar.xgrid.grid_line_color = None
        billing_frequency_bar.legend.orientation = "horizontal"
        billing_frequency_bar.legend.location = "top_center"
        
        ########################################################################################################
        # For TableColumn of Top Due_Amount Holders
        due_amount_source = ColumnDataSource(data=dict())

        def due_amount_update():
            descending_due_amount_data = data.sort_values(['due_amount'], ascending=[False]).drop_duplicates()
            # descending_due_amount_data.index = np.arange(0, len(descending_due_amount_data) + 1)
            # print(str(len(descending_due_amount_data)) + '  -  ' + str(len(due_amount_current)))
            due_amount_current = descending_due_amount_data.iloc[due_amount_slider.value[0]:due_amount_slider.value[1], :]
            due_amount_source.data = {
                'Consumer ID':       due_amount_current.consumer_id,
                'Consumer Name':     due_amount_current.consumer_name,
                'Due Amount':        due_amount_current.due_amount,
                'Billing Frequency': due_amount_current.billing_frequency,
                'Address':           due_amount_current.address
            }

        due_amount_slider = RangeSlider(title="Top Due Amount", start=0, end=100, value=(0, 10), step=10, format="0,0")
        due_amount_slider.on_change('value', lambda attr, old, new: due_amount_update())
        loc_name.on_change('value', lambda attr, old, new: due_amount_update())

        due_amount_button = Button(label="Download", button_type="success")
        due_amount_button.js_on_click(CustomJS(args=dict(source=due_amount_source),
                                    code=open(join(dirname(__file__), "download.js")).read()))

        due_amount_columns = [
            TableColumn(field="Consumer ID", title="Consumer ID"),
            TableColumn(field="Consumer Name", title="Consumer Name"),
            TableColumn(field="Due Amount", title="Due Amount", formatter=NumberFormatter(format="₹0,0.00")),
            TableColumn(field="Billing Frequency", title="Billing Frequency"),
            TableColumn(field="Address", title="Address")
        ]

        due_amount_data_table = DataTable(source=due_amount_source, columns=due_amount_columns)

        due_amount_controls = column(due_amount_slider, due_amount_button)
        
        #######################################################################################################
        # Removing Axis and Gridlines
        connection_type_pie.axis.axis_label=None
        connection_type_pie.axis.visible=False
        connection_type_pie.grid.grid_line_color = None
        connection_size_pie.axis.axis_label=None
        connection_size_pie.axis.visible=False
        connection_size_pie.grid.grid_line_color = None
        
        # Returning all the updated charts
        return connection_type_data_table, connection_type_pie, connection_size_data_table, connection_size_pie, map_chart, billing_frequency_bar, due_amount_data_table, due_amount_controls
    
    # Update the plot
    def update(attr, old, new):
        connection_type_data_table, connection_type_pie, connection_size_data_table, connection_size_pie, map_chart, billing_frequency_bar, due_amount_data_table, due_amount_controls = create_figure()
        
        # Creating the layouts for charts
        l1.children[1] = layout([[connection_type_data_table, connection_type_pie]], sizing_mode='scale_width')
        l2.children[1] = layout([[connection_size_data_table, connection_size_pie]], sizing_mode='scale_width')
        l3.children[1] = layout([[map_chart]], sizing_mode='scale_width')
        l4.children[1] = layout([[billing_frequency_bar]], sizing_mode='scale_width')
        l5.children[1] = layout([[due_amount_controls], [due_amount_data_table]], sizing_mode='scale_width')
        
        # Creating the tabs for each layout.
        tab1 = Panel(child=l1, title="Connection Type")
        tab2 = Panel(child=l2, title="Connection Size")
        tab3 = Panel(child=l3, title="Map Chart")
        tab4 = Panel(child=l4, title="Billing Frequency")
        tab5 = Panel(child=l5, title="Top Due Amount")
        
    # Controls
    available_loc_names = [i[0] for i in available_loc]
    loc_name = Select(title="Area Names :", options=available_loc_names, value=available_loc_names[0])
    
    # On change event listener when we change the region in the dropdown.
    loc_name.on_change('value', update)
    
    controls = widgetbox([loc_name], width=200)
    connection_type_data_table, connection_type_pie, connection_size_data_table, connection_size_pie, map_chart, billing_frequency_bar, due_amount_data_table, due_amount_controls = create_figure()
    
    l1 = layout([[controls], [connection_type_data_table, connection_type_pie]], sizing_mode='scale_width')
    l2 = layout([[controls], [connection_size_data_table, connection_size_pie]], sizing_mode='scale_width')
    l3 = layout([[controls], [map_chart]], sizing_mode='scale_width')
    l4 = layout([[controls], [billing_frequency_bar]], sizing_mode='scale_width')
    l5 = layout([[controls], [[due_amount_controls], [due_amount_data_table]]], sizing_mode='scale_width')
        
    tab1 = Panel(child=l1, title="connection_type")
    tab2 = Panel(child=l2, title="connection_size")
    tab3 = Panel(child=l3, title="map_chart")
    tab4 = Panel(child=l4, title="Billing Frequency")
    tab5 = Panel(child=l5, title="Top Due Amount")
    
    tabs = Tabs(tabs=[tab1, tab2, tab3, tab4, tab5])
    doc.add_root(tabs)


apps = {'/': Application(FunctionHandler(modify_doc))}
server = Server(apps, port=80, allow_websocket_origin=['*'])
# server = Server(apps, port=5006)
server.start()
server.io_loop.start()
