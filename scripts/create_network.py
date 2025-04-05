import pypsa
import pandas as pd
import plotly.express as px
import numpy as np

def find_nearest_bus(bdf, name, x, y):
    '''
    Finds the nearest bus_id from buses df

    Parameters
    ----------
    bdf : pandas dataframe
        dataframe which includes the x,y coordinates of the buses.
    name : name of generator
    

    Returns
    -------
    int
        returns the bus_id closest to the power station (heuristic)
    '''
    try:
        xbus, ybus = bdf.at[name,"X"], bdf.at[name,"Y"]

        if (xbus-x)**2 + (ybus-y)**2 < 1:
            return name, xbus, ybus
        
        else:
            nearestBus = "N/A"
            xmin,ymin = 100,100
            xbusmin,xbusmax=100,100

            for bus_name in bdf.index:
                xbus = bdf.at[bus_name,'X']
                ybus = bdf.at[bus_name,'Y']
                
                xt = x-xbus
                yt = y-ybus

                if (xt**2 + yt**2) < (xmin**2 + ymin**2): # totalmin
                    xmin,ymin = xt,yt
                    xbusmin,xbusmax = xbus,ybus
                    
                    nearestBus = bus_name

            return nearestBus,xbusmin,xbusmax

    except KeyError:
        nearestBus = "N/A"
        xmin,ymin = 100,100
        xbusmin,xbusmax=100,100

        for bus_name in bdf.index:
            xbus = bdf.at[bus_name,'X']
            ybus = bdf.at[bus_name,'Y']
            
            xt = x-xbus
            yt = y-ybus

            if (xt**2 + yt**2) < (xmin**2 + ymin**2): # totalmin
                xmin,ymin = xt,yt
                xbusmin,xbusmax = xbus,ybus
                
                nearestBus = bus_name

        return nearestBus,xbusmin,xbusmax

def nem_bubble(buses,lines,gens):
    buses = buses[buses['X'] > 135.4] # examine NEM only
    lines = lines[lines['X'] > 135.4]
    gens = gens[gens['X'] > 135.4]
    # get new locations
    lines.dropna(subset=["bus_0","bus_1"],inplace=True)
    lines[['X0','Y0']] = lines['location_0'].str.split(",",expand=True)
    lines['X0'] = lines['X0'].astype(float)
    lines['Y0'] = lines['Y0'].astype(float)
    lines[['X1','Y1']] = lines['location_1'].str.split(",",expand=True)
    lines['X1'] = lines['X1'].astype(float)
    lines['Y1'] = lines['Y1'].astype(float)
    # NEM only
    c0 = (lines.X0 > 135.4)
    c1 = (lines.X1 > 135.4)
    lines = lines.loc[c0 & c1]
    lines.reset_index(drop=True,inplace=True)
    if len(lines) == lines.name.nunique():
        print("Line names are distinct")
    return buses,lines,gens

def hobart_bubble(buses,lines,gens):
    lines.dropna(subset=["bus_0","bus_1"],inplace=True)
    lines[['X0','Y0']] = lines['location_0'].str.split(",",expand=True)
    lines['X0'] = lines['X0'].astype(float)
    lines['Y0'] = lines['Y0'].astype(float)
    lines[['X1','Y1']] = lines['location_1'].str.split(",",expand=True)
    lines['X1'] = lines['X1'].astype(float)
    lines['Y1'] = lines['Y1'].astype(float)
    buses = buses.loc[(buses['Y'] < -42.12) & (buses['X']  > 145.98)] # Hobart test case
    lines = lines.loc[(lines['Y0'] < -42.12) & (lines['X0'] > 145.98)
                & (lines['Y1'] < -42.12) & (lines['X1'] > 145.98)] # Hobart test case
    gens = gens.loc[(gens['Y'] < -42.12) & (buses['X']  > 145.98)] # Hobart test case
    return buses.copy(),lines.copy(),gens.copy()
    
def clean_buses(buses):
    # drop duplicates and substations without names
    buses = buses[~buses["name"].duplicated(keep="first")]
    buses.dropna(subset="name",inplace=True)
    buses.reset_index(drop=True,inplace=True)
    buses['rowno'] = buses.index
    # some voltages are missing, so these are added as a filler.
    # buses = buses[buses.voltagekv.isnull()]
    buses.fillna(132,inplace=True)
    # check that all bus names are distinct before setting as index.
    if buses.name.nunique()==len(buses.index):
        print("Bus names are distinct.")
        buses.set_index("name",inplace=True)
    return buses.copy()

def add_buses_to_network(buses):
    # add buses to PyPSA network
    for bus in buses.index:
        network.add("Bus",bus, v_nom = buses.at[bus,"voltagekv"])
    print("Done adding buses.")
    return buses.copy()

def add_generators_to_network(gens):
    gens.reset_index(drop=True,inplace=True)
    # check that all gen names are distinct
    if gens.name.nunique()==len(gens.index):
        print("Generator names are distinct.")
    # add generators to the PyPSA network
    for gen in gens.index:
        xc,yc = gens.at[gen,"X"],gens.at[gen,"Y"]
        bus,_,_ = find_nearest_bus(buses,gen,xc,yc)
        gens.at[gen,"nearest_bus"] = bus
        name = gens.at[gen,"name"]
        capacity = gens.at[gen,"generationmw"]
        network.add("Generator",name,bus=bus,p_max_pu=capacity)
    
    print("Done adding generators.")
    return gens.copy()

def add_lines_to_network(lines):
    # add lines to the PyPSA network
    for line in lines.index:
        name = lines.at[line,"name"] # get the full line name
        line0 = lines.at[line,"bus_0"] # gets the starting bus name
        line1 = lines.at[line,"bus_1"] # gets the destination bus name
        xc0,yc0 = lines.at[line,"X0"], lines.at[line,"Y0"]
        xc1,yc1 = lines.at[line,"X1"], lines.at[line,"Y1"]
        bus0,_,_ = find_nearest_bus(buses,line0,xc0,yc0)
        bus1,_,_ = find_nearest_bus(buses,line1,xc1,yc1)
        network.add("Line",
                    name = name,
                    bus0 = bus0,
                    bus1 = bus1,
                    x    = 0.1,
                    r    = 0.01)
    print("Done adding lines.")
    return lines.copy()

def add_loads_to_network(buses):
    # add loads
    ps = np.random.randint(50,101,len(buses))
    qs = np.random.randint(-10,11,len(buses))
    network.add("Load",network.buses.index + " load",
                bus=buses.index.to_numpy(),p_set=ps,q_set=qs,
                overwrite=True)
    return None

def add_snapshots():
    # add time varying ??
    return None

def create_interactive_map(df):
    # Create the interactive scatter map plot
    fig = px.scatter_mapbox(
        df, lat='Y', lon='X',
        size='voltagekv',  # Scale markers by size
        text=df.index,  # Show name on hover
        hover_name=df.index,  # Display name on hover
        size_max=15,  # Adjust max size for visibility
        mapbox_style= 'open-street-map'# "carto-positron",  # Choose a map style (other options: 'open-street-map', 'stamen-terrain', etc.)
    )

    # Customize layout
    fig.update_layout(
        title="Scaled Scatter Plot on Map of Australia",
        geo=dict(
            scope="asia",  # You can specify 'australia' for a more focused region if using Plotly's geo support
            center=dict(lat=-25.2744, lon=133.7751),  # Center the map on Australia
            projection_scale=10 # Adjust the zoom level for better visibility
        ),
        mapbox=dict(
            zoom=4  # Decrease zoom level
        ),
        width=1200,  # Adjust the width of the output box
        height=800  # Adjust the height of the output box
    )

    # Show interactive map plot
    fig.show()


if __name__=="__main__":
    # Load Network and Data

    network = pypsa.Network()

    buses = pd.read_csv("./data/grid/buses.csv")
    lines = pd.read_csv("./data/grid/lines.csv")
    gens = pd.read_csv("./data/grid/generators.csv")

    print(buses.head())

    print("cleaning buses")

    b = clean_buses(buses)

    print("buses are squeaky clean")

    b,l,g = hobart_bubble(b,lines,gens)

    print("creating map")

    create_interactive_map(b)

    b = add_buses_to_network(b)

    l = add_lines_to_network(l)

    g = add_generators_to_network(g)

    d = add_loads_to_network(b)

    print(network)

    print(network.pf())



    

    

