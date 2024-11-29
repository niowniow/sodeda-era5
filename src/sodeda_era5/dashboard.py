
import gradio as gr
import geoviews as gv
from .flow import Era5Flow
import holoviews as hv 
import pandas as pd 
# from holoviews.operation.datashader import regrid
import tempfile

hv.extension('bokeh')

flow = Era5Flow(store_samples=False)

def plot_map(time_start, time_end, latitude_start, latitude_end, longitude_start, longitude_end, variable):
    time_start = pd.to_datetime(time_start).isoformat()
    time_end = pd.to_datetime(time_end).isoformat()
    test_deskriptor = {
        "time": {"start": time_start, "end": time_end},
        "latitude": {"start": latitude_start, "end": latitude_end},
        "longitude": {"start": longitude_start, "end": longitude_end},
        "variable": variable,
    }
    
    data = flow(**test_deskriptor)[0]
    print(data)

    # TODO: filter for only one time step, because we cannot plot more or
    #       Fix the plotting to allow for a time slider component

    # plotting the data here!
    kdims = ["longitude", "latitude", "time"]
    # vdims = list(data.keys())
    dataset_era = gv.Dataset(data, kdims=kdims)#, vdims=vdims)
    qm = gv.project(dataset_era.to(gv.QuadMesh, ["longitude", "latitude"]))
    plot_data = (
        qm.opts(
            tools=["hover"],
            axiswise=True,
            cmap="coolwarm",
            colorbar=True,
            alpha=0.6,
        )
    )
    
    # using datashader might improve plotting
    
    # plot_data = regrid(plot_data)

    plot_map = gv.tile_sources.OSM().opts(
        title=f'ERA-5 ',
    )

    plot = plot_data * plot_map
    plot = plot.opts(width=600, height=400)
    
    bokeh_plot = hv.render(plot)

    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".zip") as temp_file:
        data.to_zarr(temp_file.name,mode="w")
        temp_file_path = temp_file.name
    
    return bokeh_plot, temp_file_path

# TODO: maybe build input boxes from scope?
scope = flow.scope()
print(scope)

with gr.Blocks() as demo:
    with gr.Column():
        with gr.Row():
            time_start = gr.DateTime(value="2023-01-01 11:00:00", label="Start time", type="string")
            time_end = gr.DateTime(value="2023-01-01 11:50:00", label="End time", type="string")
        with gr.Row():
            latitude_start = gr.Number(value=48, label="Start latitude")
            latitude_end = gr.Number(value=47, label="End latitude")
        with gr.Row():
            longitude_start = gr.Number(value=8, label="Start longitude")
            longitude_end = gr.Number(value=9, label="End longitude")
        variable = gr.CheckboxGroup(choices=["2m_temperature", "surface_pressure"], value=["2m_temperature"], label="Select Variable:")
        btn = gr.Button(value="Update Map")
        map = gr.Plot()
        output_file = gr.File(label="Download data as zarr zip file")

    demo.load(plot_map, [time_start, time_end, latitude_start, latitude_end, longitude_start, longitude_end, variable], [map,output_file])
    btn.click(plot_map, [time_start, time_end, latitude_start, latitude_end, longitude_start, longitude_end, variable], [map,output_file])

