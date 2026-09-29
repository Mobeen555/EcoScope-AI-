"""EcoScope AI 2.0: Streamlit interface for environmental tools and five CrewAI agents."""
from __future__ import annotations

import base64
import calendar
import hashlib
import html
import io
import json
import math
import os
import queue
import re
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import folium
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from pyproj import Geod, Transformer
from requests.adapters import HTTPAdapter
from shapely.geometry import Point, Polygon, mapping, shape
from shapely.geometry.polygon import orient
from shapely.ops import transform as shape_transform, unary_union
from urllib3.util.retry import Retry
from crew_config import AGENT_ROSTER, DEFAULT_MODEL, DEFAULT_TOKENS_PER_MINUTE
from evidence import quality_findings, review_is_current, run_fingerprint

from environment import (
    DataError,
    FIELD_COLUMNS,
    MAX_SAT_KM2,
    MODULES,
    PAGES,
    RASTER_STYLES,
    ROOT,
    VERSION,
    all_sources,
    all_tables,
    build_exports,
    chart_specs,
    city_search,
    execute_analysis,
    fmt,
    geotiff_bytes,
    interactive_chart,
    landmark_search,
    make_study,
    normalize_geometry,
    parse_field_csv,
    plain_metadata,
    raster_png,
    safe_frame,
    secret,
    utc_now
)


def inject_theme():
    st.html("""<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;600;700;800&display=swap');
    .stApp{background:radial-gradient(ellipse at 95% 4%,rgba(111,70,181,.22),transparent 40%),radial-gradient(ellipse at 10% 85%,rgba(16,111,115,.13),transparent 42%),#090E1B;color:#E9EEF7}
    .stApp{color-scheme:dark}
    [data-testid='stMain'],[data-testid='stSidebar']{color:#E9EEF7}
    [data-testid='stMarkdownContainer'] p,[data-testid='stMarkdownContainer'] li,[data-testid='stWidgetLabel'] p{color:#DFE9F5!important}
    [data-testid='stCaptionContainer'],[data-testid='stCaptionContainer'] p{color:#C1D0E2!important;opacity:1!important}
    [data-testid='stSidebar'] [data-testid='stCaptionContainer'] p{color:#BBCDE0!important}
    [data-testid='stMarkdownContainer'] a{color:#82EDD4!important}
    .stApp label,.stApp summary{color:#E3EDF9!important}
    .stApp input,.stApp textarea,[data-baseweb='select']>div{background-color:#172238!important;color:#F0F5FD!important;-webkit-text-fill-color:#F0F5FD}
    .stApp input::placeholder,.stApp textarea::placeholder{color:#B4C5D9!important;-webkit-text-fill-color:#B4C5D9;opacity:1}
    [role='listbox'],[role='option']{background-color:#172238!important;color:#F0F5FD!important}
    [data-testid='stAlert']{background:#142538!important;border:1px solid #58738F}
    [data-testid='stAlert'] p{color:#E8F1FB!important}
    [data-testid='stBaseButton-secondary']{background:#1C2B43!important;color:#F1F6FF!important;border:1px solid #62768D!important}
    [data-testid='stBaseButton-secondary'] p{color:#F1F6FF!important}
    [data-testid='stBaseButton-primary']{background:linear-gradient(105deg,#68E0C3,#9EADF9)!important;color:#102232!important;border:0!important}
    [data-testid='stBaseButton-primary'] p{color:#102232!important;font-weight:700}
    button:disabled{opacity:.65!important}
    html,body,[class*='css']{font-family:'DM Sans',sans-serif}
    h1,h2,h3{font-family:'Manrope',sans-serif!important;letter-spacing:-.025em}
    [data-testid='stHeader']{background:#090E1B}
    [data-testid='stSidebar']{background:linear-gradient(180deg,#12172B,#0D1C29);border-right:1px solid #243046}
    [data-testid='stSidebar'] [data-testid='stMarkdownContainer'] p{color:#B4C5D6}
    .block-container{padding-top:2rem;padding-bottom:3rem;max-width:1540px}
    [data-testid='stMetric']{background:linear-gradient(135deg,rgba(28,42,63,.92),rgba(25,27,51,.95));border:1px solid #29354D;border-radius:15px;padding:18px}
    [data-testid='stMetricValue']{color:#72E6CB;font-family:'Manrope',sans-serif}
    [data-testid='stMetricLabel']{color:#AEBED1}
    .stButton>button[kind='primary']{background:linear-gradient(105deg,#68E0C3,#9EADF9);color:#102232;border:0;font-weight:700;box-shadow:0 5px 24px #5FE1C322}
    .stButton>button,.stDownloadButton>button{border-radius:11px;min-height:2.75rem}
    [data-testid='stVerticalBlockBorderWrapper']>div{border-radius:16px}
    .eco-brand{display:flex;gap:11px;align-items:center;margin-bottom:18px}
    .eco-brand strong{font-family:Manrope,sans-serif;letter-spacing:-.6px;font-size:23px;color:#F2F6FF}.eco-brand small{display:block;font-size:10px;letter-spacing:1.7px;color:#82A2B9;text-transform:uppercase;margin-top:3px}
    .eyebrow{font-size:11px;letter-spacing:2.5px;font-weight:700;text-transform:uppercase;color:#74DEC6;margin-bottom:15px}
    .eco-hero{border-radius:24px;padding:40px;min-height:275px;border:1px solid #344663;position:relative;overflow:hidden;background:linear-gradient(140deg,#162338,#161A30)}
    .eco-hero h1{font-size:clamp(32px,3.5vw,52px);line-height:1.09;margin:10px 0 19px;color:#F6F8FF;max-width:700px}
    .eco-hero p{color:#C3D4E2;max-width:570px;font-size:15px;line-height:1.7}
    .pill{display:inline-block;border:1px solid #6FE6CB55;color:#9AF0DC;background:#18363D99;border-radius:30px;padding:5px 12px;font-size:11px;margin-right:7px;margin-top:10px}
    .eco-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin:22px 0}.eco-card{border:1px solid #28354D;background:linear-gradient(150deg,#162338,#161A30);border-radius:18px;overflow:hidden;position:relative}.eco-card .body{padding:19px}.eco-card h3{font-size:19px;color:#EBF2FD;margin:0 0 9px}.eco-card p{font-size:13px;color:#AABDD0;line-height:1.65;margin:0}.eco-card .tag{font-size:10px;letter-spacing:1.6px;color:#69DCC1;display:block;margin-bottom:8px}
    .eco-strip{display:flex;align-items:center;gap:17px;border:1px solid #2A3850;background:#14203588;border-radius:16px;padding:17px;margin:20px 0}.eco-strip strong{color:#F0F5FD;font-size:14px}.eco-strip p{font-size:13px;color:#C1D0E2;margin:3px 0 0}.eco-strip .unit{flex:1;display:flex;align-items:center;gap:12px}
    .section-note{color:#9CB1C5;font-size:13px;line-height:1.7}.status-chip{display:inline-block;color:#A8EBD8;background:#123B3880;border:1px solid #286858;border-radius:20px;padding:5px 12px;font-size:11px;margin:6px 0 16px}
    .module-banner{min-height:100px;border:1px solid #33475B;border-radius:18px;padding:23px 28px;background:linear-gradient(140deg,#162338,#161A30);position:relative;margin:12px 0 23px}.module-banner h2{color:#F4F8FE;margin:0;font-size:26px}.module-banner p{color:#C8D8E7;font-size:12px;margin:7px 0}
    [data-testid='stDataFrame']{border:1px solid #29384D;border-radius:12px;overflow:hidden}
    [class*='st-key-card-'],[class*='st-key-info-']{border-radius:18px;background:linear-gradient(145deg,#162338,#161A30)}
    .card-copy h3{color:#EBF2FD;margin:4px 0 10px;font-size:19px}.card-copy p{color:#C1D0E2;font-size:13px;line-height:1.65}.card-copy .tag{color:#74DEC6;font-size:10px;letter-spacing:1.6px}
    .card-copy strong{color:#F0F5FD}
    @media(max-width:900px){.eco-grid{grid-template-columns:1fr}.eco-hero{padding:25px}.eco-strip{flex-direction:column;align-items:stretch}}
    </style>""")


def go_page(page):
    st.session_state["page"] = page


def apply_drawing(drawing):
    try:
        st.session_state["boundary"] = mapping(normalize_geometry(drawing))
        st.session_state["use_boundary"] = True
    except DataError as exc:
        st.session_state["drawing_error"] = str(exc)


def banner(title, subtitle):
    st.html(f"<div class='module-banner'><h2>{html.escape(title)}</h2><p>{html.escape(subtitle)}</p></div>")


def overview(run):
    st.html("""<div class='eco-hero'>
        <div class='eyebrow'>Planetary data. Local understanding.</div><h1>See the environment.<br>Understand the evidence.</h1>
        <p>Explore satellite observations, climate patterns and ecological records in one place. Turn your study area into maps, analysis and a report you can trace to its sources.</p>
        <span class='pill'>Satellite + GIS</span><span class='pill'>Climate + water</span><span class='pill'>AI-assisted analysis</span></div>""")
    st.write("")
    c1,c2,c3 = st.columns(3)
    c1.button("Start a new analysis", type="primary", width="stretch", on_click=go_page, args=("Study & analysis",))
    c2.button("Open reports", width="stretch", on_click=go_page, args=("Reports & sources",))
    c3.button("Open AI team", width="stretch", on_click=go_page, args=("AI team",))
    cards = [
        ("01 / EARTH OBSERVATION", "Satellite & water", "Inspect real Sentinel-2 scenes, screened water extent, vegetation and optical water indicators."),
        ("02 / SPATIAL CONTEXT", "Maps that explain", "Draw a study boundary, inspect layers and export georeferenced results for QGIS."),
        ("03 / LIVING SYSTEMS", "Ecology & field evidence", "Explore recorded species and connect your own water-sampling observations to the map."),
    ]
    for i, (column, (tag, title, desc)) in enumerate(zip(st.columns(3), cards)):
        with column:
            with st.container(border=True, key=f"card-{i}"):
                st.html(f"<div class='card-copy'><span class='tag'>{tag}</span><h3>{title}</h3><p>{desc}</p></div>")
    infos = [("Traceable observations", "Acquisition date, resolution and processing method."),
             ("A defined study area", "Coordinates, a drawn polygon or a GeoJSON boundary."),
             ("Evidence for decisions", "Charts, tables, maps and practical follow-up.")]
    for i, (column, (title, desc)) in enumerate(zip(st.columns(3), infos)):
        with column:
            with st.container(border=True, key=f"info-{i}"):
                st.html(f"<div class='card-copy'><strong>{title}</strong><p>{desc}</p></div>")
    if run:
        st.subheader("Your latest analysis")
        st.caption(f"{run['study']['label']} · {run['study']['start']} to {run['study']['end']} · Run {run['id']}")
        c1,c2,c3 = st.columns(3)
        c1.metric("Completed modules", len(run["results"]))
        c2.metric("Study area", f"{run['study']['area_km2']:.1f} km²")
        c3.metric("Source records", len(all_sources(run)))
        for r in list(run["results"].values())[:3]:
            if r["facts"]:
                st.write(r["facts"][0])
    else:
        with st.container(border=True):
            st.markdown("**Begin with a place you know.**")
            st.write("The default study is around Rawal Lake, Islamabad. Adjust its boundary and dates, choose your modules, and run the analysis. No environmental values appear until data are retrieved.")
    st.caption("Research MVP · latest available data may have acquisition or processing delays · official authorities remain the source for emergency warnings")


def base_map(study, draw=False):
    from folium.plugins import Draw, Fullscreen
    m = folium.Map(location=[study["lat"], study["lon"]], tiles="OpenStreetMap", zoom_start=12, control_scale=True)
    folium.GeoJson(study["geometry"], name="Study boundary", style_function=lambda _: {"color": "#A78BFA", "weight": 3, "fillColor": "#5FE1C3", "fillOpacity": .09}).add_to(m)
    west,south,east,north = study["bbox"]
    m.fit_bounds([[south,west],[north,east]])
    Fullscreen().add_to(m)
    if draw:
        Draw(export=False, draw_options={"polyline": False, "circle": False, "circlemarker": False, "marker": False,
             "polygon": {"allowIntersection": False}, "rectangle": True}, edit_options={"edit": False, "remove": True}).add_to(m)
    return m


def map_for_run(run, modules=None, raster_layer=None):
    m = base_map(run["study"])
    modules = modules or list(run["results"])
    for module, table_name, frame in all_tables(run):
        if module not in modules or table_name not in ["Sampling candidates", "Included field observations", "Earthquake events", "Species occurrences"] or frame.empty:
            continue
        group = folium.FeatureGroup(name=table_name)
        for _, row in frame.iterrows():
            radius, color, title = 6, "#128C80", table_name
            if table_name == "Earthquake events":
                mag = float(row.magnitude) if pd.notna(row.magnitude) else 0
                radius, color, title = 2 + 1.6*max(0,mag), "#8A5CD1", f"Magnitude {fmt(mag,1)} · depth {fmt(row.depth_km,1)} km"
            elif table_name == "Species occurrences":
                title, color, radius = str(row.species), "#579242", 4
            elif table_name == "Sampling candidates":
                title, color = f"Candidate {row.priority_rank} · NDCI {row.ndci:.3f} (unverified)", "#B98013"
            elif table_name == "Included field observations":
                title = str(row.site)
                if "chlorophyll_ug_l" in row and pd.notna(row.chlorophyll_ug_l):
                    # Area proportional to measurement, with readable bounds.
                    radius = min(22, max(4, math.sqrt(max(0,float(row.chlorophyll_ug_l))) * 2))
                    title += f" · chlorophyll {row.chlorophyll_ug_l:g} µg/L (user supplied)"
            folium.CircleMarker([row.latitude, row.longitude], radius=radius, color=color, weight=1,
                fill=True, fill_color=color, fill_opacity=.75, tooltip=html.escape(title)).add_to(group)
        group.add_to(m)
        if modules == ["Earthquakes"]:
            m.fit_bounds([[frame.latitude.min(),frame.longitude.min()],[frame.latitude.max(),frame.longitude.max()]])
    if raster_layer:
        r = run["results"].get("Satellite", {}).get("raster")
        if r and np.isfinite(r["arrays"][raster_layer]).any():
            from affine import Affine
            from rasterio.warp import calculate_default_transform, reproject, Resampling, transform_bounds
            from rasterio.transform import array_bounds
            h,w = r["valid"].shape
            src_transform = Affine(*r["transform"][:6])
            bounds = array_bounds(h,w,src_transform)
            dst_transform,dw,dh = calculate_default_transform(f"EPSG:{r['epsg']}", "EPSG:3857", w,h,*bounds)
            source = r["arrays"][raster_layer]
            dest = np.full((dh,dw),np.nan,dtype="float32")
            reproject(source,dest,src_transform=src_transform,src_crs=f"EPSG:{r['epsg']}",src_nodata=np.nan,
                      dst_transform=dst_transform,dst_crs="EPSG:3857",dst_nodata=np.nan,resampling=Resampling.nearest)
            cmap,lo,hi = RASTER_STYLES[raster_layer]
            rgba = matplotlib.colormaps[cmap](np.clip((np.nan_to_num(dest)-lo)/(hi-lo),0,1))
            rgba[:,:,3] = np.isfinite(dest)*.82
            west,south,east,north = transform_bounds("EPSG:3857","EPSG:4326",*array_bounds(dh,dw,dst_transform))
            folium.raster_layers.ImageOverlay((rgba*255).astype("uint8"), bounds=[[south,west],[north,east]], name=raster_layer, opacity=.9).add_to(m)
            from branca.colormap import LinearColormap
            colors = [matplotlib.colors.to_hex(matplotlib.colormaps[cmap](v)) for v in np.linspace(0,1,8)]
            LinearColormap(colors,vmin=lo,vmax=hi,caption=f"{raster_layer} · screening index").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def show_map(m, key, height=475, interactive=False):
    from streamlit_folium import st_folium
    return st_folium(m, height=height, use_container_width=True, key=key,
                     returned_objects=["last_active_drawing"] if interactive else [])


def study_page():
    st.title("Define your study")
    st.caption("Choose a place, inspect the boundary and request only the evidence you need.")
    left,right = st.columns([1,1.65], gap="large")
    with left:
        with st.expander("Find a city, lake or landmark", expanded=True):
            query = st.text_input("Place name", placeholder="Rawal Lake, Islamabad")
            landmarks = st.checkbox("Include river / landmark search using OpenStreetMap", value=False)
            if landmarks:
                st.caption("User-triggered searches only, cached and limited to one request per second for this app; no autocomplete. OpenStreetMap attribution applies.")
                st.markdown("[Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/)")
            if st.button("Search place", width="stretch"):
                if len(query.strip()) < 3:
                    st.warning("Enter at least three characters.")
                else:
                    try:
                        with st.spinner("Finding matching places…"):
                            st.session_state["places"] = landmark_search(query.strip()) if landmarks else city_search(query.strip())
                    except DataError as exc:
                        st.error(str(exc))
            places = st.session_state.get("places", [])
            if places:
                chosen = st.selectbox("Matching places", range(len(places)), format_func=lambda i: places[i]["label"])
                if st.button("Use this location"):
                    p = places[chosen]
                    st.session_state.update({"study_lat": p["lat"], "study_lon": p["lon"], "study_label": p["label"], "use_boundary": False})
            elif "places" in st.session_state:
                st.caption("No matching place. Use coordinates or try the landmark search.")
        label = st.text_input("Study name", key="study_label")
        st.caption("A study name labels the result. It does not select the entire river or change the coordinates.")
        a,b = st.columns(2)
        lat = a.number_input("Latitude", min_value=-80.0,max_value=80.0,format="%.6f",key="study_lat")
        lon = b.number_input("Longitude",min_value=-180.0,max_value=180.0,format="%.6f",key="study_lon")
        radius = st.slider("Study radius (km)",.5,50.0,4.0,.5)
        start = st.date_input("Historical start", date.today()-timedelta(days=97),max_value=date.today())
        end = st.date_input("Historical end", date.today()-timedelta(days=7),max_value=date.today())
        st.caption("Weather and air forecasts start today; they use a separate future window.")
        upload = st.file_uploader("Optional boundary (GeoJSON, WGS84)",type=["geojson","json"])
        if upload is not None:
            try:
                if upload.size > 2_000_000:
                    raise DataError("Keep boundary uploads below 2 MB.")
                parsed = json.loads(upload.getvalue())
                st.session_state["boundary"] = mapping(normalize_geometry(parsed))
            except Exception as exc:
                st.error(f"Boundary could not be used: {str(exc)[:200]}")
        custom = None
        if st.session_state.get("boundary"):
            if st.checkbox("Use uploaded / drawn boundary", key="use_boundary"):
                custom = st.session_state["boundary"]
        try:
            study = make_study(label,lat,lon,radius,start,end,custom)
        except DataError as exc:
            st.error(str(exc))
            study = None
    with right:
        if study:
            response = show_map(base_map(study, True),"draw-study",height=505,interactive=True)
            drawing = (response or {}).get("last_active_drawing")
            if drawing:
                st.button("Use the drawn boundary",type="primary",on_click=apply_drawing,args=(drawing,))
            if st.session_state.get("drawing_error"):
                st.error(st.session_state.pop("drawing_error"))
            st.caption(f"{study['area_km2']:.2f} km² · {study['boundary']} · Weather/air use the centroid grid cell. Drawing a boundary does not delineate an upstream catchment.")
            st.info(f"Local study centred at {study['lat']:.5f}, {study['lon']:.5f}. For a river, zoom in and check that the boundary actually covers the intended channel or reach. A geocoding result is a reference point, not a river boundary.")
            if study["area_km2"] > MAX_SAT_KM2:
                st.info(f"Satellite analysis supports up to {MAX_SAT_KM2:g} km². Other selected modules can still run.")
    st.subheader("Select analyses")
    selected = st.multiselect("Modules",MODULES,default=["Climate","Air quality","Satellite","Earthquakes","Biodiversity"])
    with st.expander("Analysis settings",expanded=False):
        c1,c2,c3 = st.columns(3)
        with c1:
            baseline = st.checkbox("Add 1991–2020 climate baseline",False)
            st.caption("Uses a longer ERA5 request. Monthly anomalies require complete months.")
            flow = st.number_input("Optional river screening threshold (m³/s)",min_value=0.0,value=0.0)
            st.caption("0 disables threshold comparisons. A supplied threshold is not automatically validated.")
        with c2:
            scenes = st.slider("Satellite scenes to process",1,6,3)
            cloud = st.slider("Maximum whole-scene cloud cover (%)",5,90,40,5)
            water = st.slider("NDWI / MNDWI water screening threshold",-.2,.4,0.0,.05)
        with c3:
            quake_radius = st.slider("Earthquake search radius (km)",25,500,150,25)
            magnitude = st.slider("Minimum earthquake magnitude",0.0,7.0,2.5,.5)
            st.caption("Earthquake radius is separate from the study boundary. GBIF retrieval is limited to 300 candidate records.")
    if "US weather alerts" in selected:
        st.info("The official alert adapter supports US NWS coverage. Outside that area, check your national authority; an empty response does not mean no hazard.")
    if st.button("Run environmental analysis",type="primary",width="stretch",disabled=study is None):
        if not selected:
            st.warning("Select at least one module.")
        else:
            options = {"modules":selected,"baseline":baseline,"flow_threshold":flow,"scene_count":scenes,
                       "cloud_limit":cloud,"water_threshold":water,"quake_radius":quake_radius,"min_magnitude":magnitude}
            with st.status("Gathering evidence…",expanded=True) as status:
                run = execute_analysis(study,options,lambda text: st.write(text))
                st.session_state["run"] = run
                st.session_state.pop("exports",None)
                st.session_state.pop("crew_review",None)
                status.update(label=f"{len(run['results'])} modules completed · {len(run['errors'])} unavailable",state="complete" if run["results"] else "error",expanded=False)
            for name, error in run["errors"].items():
                st.warning(f"{name}: {error}")
            if run["results"]:
                st.success("Analysis saved for this session. Open the result pages or generate your report.")
                st.button("Explore satellite & water",on_click=go_page,args=("Satellite & water",))


def need_run(run):
    if run:
        st.caption(f"Viewing run {run['id']} · {run['study']['label']} · historical period {run['study']['start']} to {run['study']['end']}")
        return True
    st.info("Run an analysis first. Each results page uses the saved study boundary and dates.")
    st.button("Set up your study",type="primary",on_click=go_page,args=("Study & analysis",))
    return False


def module_view(run, module, charts=True):
    r = run["results"].get(module)
    if not r:
        message = run["errors"].get(module,"This module was not selected in the saved analysis.")
        st.info(f"{module}: {message}")
        return
    st.subheader(module)
    metrics = list(r["metrics"].items())
    if metrics:
        cols = st.columns(min(3,len(metrics)))
        for i,(name,value) in enumerate(metrics):
            cols[i%len(cols)].metric(name,fmt(value,1))
    for fact in r["facts"]:
        st.write(fact)
    if charts:
        for spec in chart_specs(run):
            if spec["module"] == module:
                st.markdown(f"**{spec['title']}**")
                st.plotly_chart(interactive_chart(spec),width="stretch",key=f"chart-{module}-{spec['table']}-{spec['ys'][0]}")
                st.caption("Evidence: " + spec["evidence"])
    with st.expander("Data tables and CSV downloads"):
        for title,frame in r["tables"].items():
            st.markdown(f"**{title}** · {len(frame):,} rows")
            st.dataframe(frame,width="stretch",hide_index=True)
            st.download_button("Download " + title,safe_frame(frame).to_csv(index=False).encode("utf-8-sig"),
                file_name=re.sub(r"\W+","_",title.lower())+".csv",mime="text/csv",key=f"csv-{module}-{title}")
    with st.expander("Methods, coverage and limitations",expanded=module in ["Satellite","River outlook"]):
        for note in r["notes"]:
            st.write("• " + note)
        st.dataframe(pd.DataFrame(r["sources"]),width="stretch",hide_index=True)


def satellite_page(run):
    banner("Satellite & water","Surface observations, optical screening and areas to investigate.")
    if not need_run(run):
        return
    r = run["results"].get("Satellite",{}).get("raster")
    if r:
        available_layers = [name for name in RASTER_STYLES if np.isfinite(r["arrays"][name]).any()]
        if r["summary"]["water_pixels"] == 0:
            st.warning("No pixels passed the water screen in the latest scene. NDCI and water reflectance are unavailable. Inspect the boundary, true-colour image, an earlier date and the screening settings; do not interpret this as clean or absent water.")
        if r["summary"]["valid_aoi_percent"] < 50:
            st.warning(f"Latest usable coverage: {r['summary']['valid_aoi_percent']:.1f}% of the study area. The masked portion has no usable result.")
        layer = st.selectbox("Map layer", available_layers) if available_layers else None
        show_map(map_for_run(run,["Satellite","Field observations"],layer),f"sat-map-{run['id']}-{layer}",height=530)
        st.caption(f"Actual processed satellite layer · {r['summary']['date']} · {r['resolution']} m common grid. Blank pixels are masked/no data. Golden points are unverified sampling candidates.")
        with st.expander("True-colour view and exportable GIS raster"):
            st.image(raster_png(r,"True colour"),width="stretch")
            st.download_button("Download all indices as GeoTIFF",geotiff_bytes(r),file_name="ecoscope_satellite_indices.tif",mime="image/tiff")
    module_view(run,"Satellite")
    st.info("For measured eutrophication indicators, upload field samples on Ecology & field. Satellite indices alone do not establish nutrient concentration, toxicity or drinking-water safety.")


def climate_page(run):
    banner("Climate & air","Historical context and clearly dated model forecasts.")
    if need_run(run):
        module_view(run,"Climate")
        st.divider()
        module_view(run,"Air quality")


def hazards_page(run):
    banner("Hazards & outlooks","River-flow forecasts, earthquake observations and supported official alerts.")
    if not need_run(run):
        return
    st.warning("EcoScope is a research workbench. Discharge forecasts are not inundation maps; earthquake event histories do not predict future events.")
    choice = st.radio("Hazard view",["River outlook","Earthquakes","US weather alerts"],horizontal=True)
    if choice == "Earthquakes" and choice in run["results"]:
        show_map(map_for_run(run,["Earthquakes"]),"earthquake-map-"+run["id"])
        st.caption("Bubble radius follows catalogue magnitude; event depth and magnitude are available on hover. The catalogue may omit smaller events.")
    module_view(run,choice)
    st.markdown("Official Pakistan advisories: [PMD](https://www.pmd.gov.pk/) · [NDMA](https://www.ndma.gov.pk/). Official US alerts: [National Weather Service](https://www.weather.gov/).")


def ecology_page(run):
    banner("Ecology & citizen evidence","Connect recorded biodiversity with measurements collected on the ground.")
    if not need_run(run):
        return
    st.subheader("Add field measurements")
    st.caption("Required columns: site, date, latitude, longitude. Optional measurement names include their units. Use blanks for missing values.")
    template = ",".join(FIELD_COLUMNS)+"\n"
    st.download_button("Download blank field CSV template",template,"field_samples_template.csv","text/csv")
    samples = st.file_uploader("Upload field observations (CSV)",type=["csv"],key="field_csv")
    lake = st.checkbox("Calculate separate Carlson indices for appropriate lake / reservoir samples",False)
    if st.button("Validate and attach observations",disabled=samples is None):
        try:
            observations = parse_field_csv(samples.getvalue(),run["study"],lake)
            run["results"]["Field observations"] = observations
            run["field_updated_utc"] = utc_now()
            st.session_state["run"] = run
            st.session_state.pop("exports",None)
            st.session_state.pop("crew_review",None)
            st.success("Observations attached to this run. Out-of-area/date rows are retained in the audit table and excluded from analysis.")
        except DataError as exc:
            st.error(str(exc))
    if "Field observations" in run["results"]:
        if st.button("Remove attached observations"):
            del run["results"]["Field observations"]
            st.session_state.pop("exports",None)
            st.session_state.pop("crew_review",None)
            st.rerun()
    show_map(map_for_run(run,["Biodiversity","Field observations","Satellite"]),"ecology-map-"+run["id"])
    st.caption("Uploaded chlorophyll measurements use proportional bubble areas, capped for readability. Species points show recorded observations; sampling candidates remain unverified.")
    module_view(run,"Field observations")
    module_view(run,"Biodiversity")


def ai_page(run):
    st.title("Your five-agent environmental team")
    st.caption("CrewAI · Sequential workflow · Coordinator, three specialists, then evidence review and report writing.")
    st.dataframe(pd.DataFrame([{"Agent": role, "Responsibility": description} for _,role,description in AGENT_ROSTER]),
                 hide_index=True, width="stretch")
    with st.expander("AI connection and privacy",expanded=not bool(secret("GROQ_API_KEY"))):
        key = secret("GROQ_API_KEY")
        if not key:
            key = st.text_input("Groq API key (private, session only)",type="password",value=st.session_state.get("_groq_key", ""))
            st.session_state["_groq_key"] = key
        model = st.text_input("Groq model",value=secret("GROQ_MODEL",DEFAULT_MODEL))
        tokens_per_minute = st.number_input("Estimated token budget per minute",min_value=2000,max_value=100000,
            value=DEFAULT_TOKENS_PER_MINUTE,step=1000,
            help="Set this at or below your Groq account's limit. All five agents share the budget. The estimate includes reserved response tokens; other apps using your key can still cause rate limits.")
        st.caption("One Groq key serves all five agents. Environmental analysis and standard reports work without a key. Only the question, study metadata, summaries and requested statistics are sent; raw rasters and uploaded files are not sent. Keys are excluded from reports.")
        st.markdown("[Create a Groq API key](https://console.groq.com/keys)")
        st.success("Key supplied. The connection is checked when you start the team.") if key else st.info("Add a Groq key here or set GROQ_API_KEY in Streamlit Secrets to enable the team.")
    if not need_run(run):
        return
    with st.expander("Evidence coverage before AI review"):
        st.dataframe(pd.DataFrame(quality_findings(run)),hide_index=True,width="stretch")
    consent = st.checkbox("Allow this run's summaries, study coordinates and requested statistics to be sent to Groq",False)
    question = st.text_area("Question for the team",value="Assess the available environmental evidence for this study. Explain the strongest findings, missing evidence and practical next steps.",height=120,max_chars=2000)
    st.caption("The team reviews the saved analysis. Run new environmental analysis to change location, dates or source data. A review can take several minutes while API requests are paced.")
    if st.button("Run five-agent review",type="primary",disabled=not consent or not key or not run["results"]):
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            try:
                from crew_workflow import run_team
                from crew_runtime import CrewRunError
                with st.status("The five-agent review is running…",expanded=True) as status:
                    def progress(event):
                        if event["event"] == "completed":
                            status.write(f"{event['stage']}/5 complete — {event['role']}")
                        elif event["event"] == "rate_pause":
                            status.update(label=f"Pacing API requests — approximately {event['seconds']} seconds until the next slot")
                        elif event["event"] == "model_request":
                            status.update(label=f"Review in progress — model request {event['call']}")
                    # CrewAI may invoke callbacks on its own worker threads.
                    # Only the Streamlit script thread may update the interface.
                    events = queue.Queue()
                    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="ecoscope-review") as pool:
                        future = pool.submit(run_team,run,question,key,model,int(tokens_per_minute),events.put)
                        while not future.done():
                            try:
                                progress(events.get(timeout=.15))
                            except queue.Empty:
                                pass
                        while not events.empty():
                            progress(events.get_nowait())
                        review = future.result()
                    status.update(label="Five-agent review complete" if review["status"] == "complete" else "Review stopped; partial notes retained",
                                  state="complete" if review["status"] == "complete" else "error",expanded=False)
                st.session_state["crew_review"] = review
                st.session_state.pop("exports",None)
            except ImportError:
                st.error("CrewAI is not installed correctly. Upload this package's requirements.txt and all Python files, then reboot the app.")
            except (DataError, ValueError) as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(str(exc) if type(exc).__name__ == "CrewRunError" else "The AI team could not start. Check the supplied files, dependency versions and Groq settings. Environmental results are preserved.")
    reply = st.session_state.get("crew_review")
    if reply and reply.get("fingerprint") != run_fingerprint(run):
        st.info("The saved AI review belongs to different evidence. Run the team again for this analysis.")
    elif reply:
        if reply["status"] == "complete":
            st.markdown(reply["answer"])
            st.success("All five agents completed. The AI narrative can now be included under Reports & sources.")
        else:
            st.warning(reply.get("error", "The AI review did not complete."))
            st.caption("These are partial agent notes, not a completed final review.")
        st.caption("AI-generated interpretation. The reviewer checks available evidence but does not independently validate scientific accuracy. Verify cited findings before sharing.")
        for note in reply.get("agent_outputs",[]):
            with st.expander(note["role"]):
                st.markdown(note["text"])
        with st.expander("Team activity and request usage"):
            st.json(reply.get("usage",{}))
            st.dataframe(pd.DataFrame(reply.get("activity",[])),hide_index=True,width="stretch")
        st.download_button("Download agent review and activity",json.dumps(reply,indent=2,ensure_ascii=False),
                           "ecoscope_five_agent_review.json","application/json")
        if reply["status"] == "complete":
            st.download_button("Download final AI narrative",reply["answer"],"ecoscope_ai_review.md","text/markdown")
    st.subheader("Evidence available without AI")
    for r in run["results"].values():
        for fact in r["facts"]:
            st.write(fact)


@st.cache_resource
def report_lock():
    return threading.Lock()


def reports_page(run):
    st.title("Reports & source records")
    st.caption("A shareable report, full data tables and GIS-ready layers from the same saved analysis.")
    if not need_run(run):
        return
    c1,c2,c3 = st.columns(3)
    c1.metric("Completed modules",len(run["results"]))
    c2.metric("Data tables",len(all_tables(run)))
    c3.metric("Source records",len(all_sources(run)))
    st.write("The report includes findings, maps, charts, table previews, methods, limitations and source records. The complete ZIP includes every returned table, PNG figures, GeoJSON, metadata and a GeoTIFF when satellite processing succeeds.")
    review = st.session_state.get("crew_review")
    include_ai = False
    if review_is_current(run,review):
        include_ai = st.checkbox("Include the completed five-agent AI review",value=True)
    else:
        st.caption("Run the team under AI team to add a completed AI narrative. The standard evidence report is available now.")
    export_run = {**run, "crew_review": review} if include_ai else run
    export_key = (run_fingerprint(run), review.get("generated_utc") if include_ai else None)
    if st.button("Generate report & export package",type="primary",width="stretch"):
        try:
            with st.spinner("Rendering charts, maps, PDF and workbook…"):
                with report_lock():
                    exports = build_exports(export_run)
            st.session_state["exports"] = {"run":run["id"],"export_key":export_key,"files":exports}
        except Exception as exc:
            st.error(f"Export could not complete ({type(exc).__name__}). Your analysis is still available. Individual CSV and GeoTIFF downloads can be used while the report issue is resolved.")
    bundle = st.session_state.get("exports")
    if bundle and bundle.get("export_key") == export_key:
        ex = bundle["files"]
        c1,c2,c3,c4 = st.columns(4)
        suffix = run["id"]
        c1.download_button("Complete ZIP",ex["zip"],f"ecoscope_{suffix}.zip","application/zip",width="stretch",type="primary")
        c2.download_button("PDF report",ex["pdf"],f"ecoscope_{suffix}.pdf","application/pdf",width="stretch")
        c3.download_button("HTML report",ex["html"],f"ecoscope_{suffix}.html","text/html",width="stretch")
        c4.download_button("Excel data",ex["xlsx"],f"ecoscope_{suffix}.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",width="stretch")
        st.success("Exports are ready. Download them before ending the session; this MVP does not provide a persistent project database.")
    st.subheader("Provenance")
    st.dataframe(pd.DataFrame(all_sources(run)),width="stretch",hide_index=True)
    st.download_button("Download run metadata",json.dumps(plain_metadata(run),indent=2,default=str),"metadata.json","application/json")
    if run["errors"]:
        st.subheader("Unavailable modules")
        for module,error in run["errors"].items():
            st.warning(f"{module}: {error}")
    with st.expander("Data access, attribution and operational limits"):
        st.write("Open-Meteo hosted free access is for non-commercial use and has quotas. Include attribution to Open-Meteo and the underlying data providers. Sentinel imagery: Copernicus Sentinel data via Earth Search. GBIF records retain contributor and licence fields. Maps: © OpenStreetMap contributors.")
        st.write("The app caches public provider responses and limits retries and satellite processing. Satellite scenes may be old or cloudy, and coarse model grids cannot resolve every local condition. Baselines, forecasts and observations are labelled separately.")
        st.write("Scope: bounded-area research MVP. Persistent multi-user projects, validated local flood models, calibrated water-quality concentrations and autonomous emergency alerts require additional infrastructure and validation.")
        st.markdown("[Open-Meteo terms](https://open-meteo.com/en/terms) · [Open-Meteo pricing/access](https://open-meteo.com/en/pricing) · [OpenStreetMap attribution](https://www.openstreetmap.org/copyright)")


def main():
    st.set_page_config(page_title="EcoScope AI | Environmental intelligence",layout="wide",initial_sidebar_state="expanded")
    inject_theme()
    for key,value in {"study_label":"Rawal Lake, Islamabad","study_lat":33.700,"study_lon":73.120,"page":"Overview","use_boundary":False}.items():
        if key not in st.session_state:
            st.session_state[key] = value
    with st.sidebar:
        st.html("<div class='eco-brand'><div><strong>EcoScope <span style='color:#72E2C9'>AI</span></strong><small>Environmental intelligence</small></div></div>")
        page = st.radio("Workspace",PAGES,key="page",label_visibility="collapsed")
        st.divider()
        run = st.session_state.get("run")
        if run:
            st.caption("SAVED ANALYSIS")
            st.markdown(f"**{run['study']['label']}**")
            st.caption(f"{run['study']['start']} → {run['study']['end']}")
            st.caption(f"{len(run['results'])} modules · {len(run['errors'])} unavailable")
            st.caption("Retrieved times appear in source records.")
        else:
            st.caption("READY WHEN YOU ARE")
            st.write("Begin with a place and a question.")
        st.divider()
        st.caption(f"v{VERSION} · CrewAI · 5 agents")
        st.caption("Open data • Reproducible methods • Clear uncertainty")
    c1, c2, c3 = st.columns([2.6, 1, 1])
    c1.caption(f"ECOSCOPE AI {VERSION} · {page}")
    c2.button("AI team", width="stretch", key="always-ai", on_click=go_page, args=("AI team",))
    c3.button("Study setup", width="stretch", key="always-study", on_click=go_page, args=("Study & analysis",))
    if run and run.get("version") != VERSION:
        st.warning("This saved analysis was generated by an earlier app version. Run environmental analysis again before using the new AI team and reports.")
        run = None
    if page == "Overview": overview(run)
    elif page == "Study & analysis": study_page()
    elif page == "Satellite & water": satellite_page(run)
    elif page == "Climate & air": climate_page(run)
    elif page == "Hazards": hazards_page(run)
    elif page == "Ecology & field": ecology_page(run)
    elif page == "AI team": ai_page(run)
    else: reports_page(run)


if __name__ == "__main__":
    main()
