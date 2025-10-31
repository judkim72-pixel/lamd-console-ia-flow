
import json, math, io, os
import streamlit as st
from typing import Dict, List, Any, Tuple
from streamlit.components.v1 import html as st_html

st.set_page_config(page_title="UI Architect — PPT-style IA & Flow (v2)", layout="wide")
st.title("UI Architect — PPT-style IA & Flow (v2)")
st.caption("Zoom & scroll improved. Use sliders to fit your screen.")

# ----------------------------
# SVG helpers
# ----------------------------
def svg_header(w:int, h:int) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
def svg_footer() -> str:
    return "</svg>"
def rect(x,y,w,h,rx=12,ry=12,fill="#FFFFFF",stroke="#222",sw=1.4) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def text(x,y,s,anchor="start",size=14,fill="#111",weight="400") -> str:
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}" font-family="Segoe UI, Arial, Helvetica">{s}</text>'
def line(x1,y1,x2,y2,stroke="#999",sw=1.2) -> str:
    return f'<line x1="{x1}" y="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"/>'
def arrow(x1,y1,x2,y2,color="#555",sw=1.4) -> str:
    seg = line(x1,y1,x2,y2,color,sw)
    ang = math.atan2(y2-y1, x2-x1)
    hx1 = x2 - 9*math.cos(ang - math.pi/6); hy1 = y2 - 9*math.sin(ang - math.pi/6)
    hx2 = x2 - 9*math.cos(ang + math.pi/6); hy2 = y2 - 9*math.sin(ang + math.pi/6)
    head = f'<path d="M{x2},{y2} L{hx1},{hy1} L{hx2},{hy2} Z" fill="{color}"/>'
    return seg + head
def diamond(cx,cy,w,h,fill="#FFF7E6",stroke="#C88600",sw=1.4):
    pts = [(cx,cy-h/2),(cx+w/2,cy),(cx,cy+h/2),(cx-w/2,cy)]
    pts_s = " ".join([f"{px},{py}" for px,py in pts])
    return f'<polygon points="{pts_s}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

def wrap_lines(s:str, max_chars:int=28) -> List[str]:
    words = s.split()
    lines, cur = [], ""
    for w in words:
        if len(cur)+len(w)+1 <= max_chars:
            cur = (cur+" "+w).strip()
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines or [""]

# ----------------------------
# Default sample (ASCII-safe)
# ----------------------------
default_spec = {
  "project": {"title": "LAMD Left Panel - IA & Flows", "author": "AEON Communications", "version": "v1.0"},
  "canvas": {"width": 1600, "height": 900, "theme": {"bg":"#FAFAFC","ink":"#111","accent":"#2B6CB0","muted":"#999"}},
  "ia": {
    "scope": ["Left Graphic Panel Only", "27\" FHD (1920x1080)", "Avoid red alerts", "Security labels required"],
    "zones": [
      {"id": "Z5", "label": "System Status", "x": 40, "y": 80, "w": 1500, "h": 50, "fill":"#FFF7F0"},
      {"id": "Z2", "label": "Layer Controls", "x": 40, "y": 140, "w": 220, "h": 650, "fill":"#F3F7FF"},
      {"id": "Z3", "label": "KPI Mini-View", "x": 280, "y": 140, "w": 280, "h": 150, "fill":"#FFFDE7"},
      {"id": "Z4", "label": "Legend & Scale", "x": 280, "y": 770, "w": 1260, "h": 40, "fill":"#EEF9FF"},
      {"id": "Z1", "label": "Main Canvas", "x": 280, "y": 310, "w": 1260, "h": 450, "fill":"#EEF5EE"}
    ],
    "components": [
      {"zone":"Z1", "title":"Range x Altitude Grid", "id":"C-Grid"},
      {"zone":"Z1", "title":"Track Symbols & Height Bars", "id":"C-TrackBars"},
      {"zone":"Z1", "title":"Motion Trails (6-12s)", "id":"C-Trails"},
      {"zone":"Z1", "title":"FOV/Engagement Bands", "id":"C-FOV"},
      {"zone":"Z2", "title":"Layer Toggles (2.5D/Trail/FOV)", "id":"C-Layers"},
      {"zone":"Z3", "title":"KPI Badges (TSA/FPS/Misassoc)", "id":"C-KPI"},
      {"zone":"Z5", "title":"FPS/lag_ms/rollback", "id":"C-Status"},
      {"zone":"Z4", "title":"Legend/Units/Abbrev", "id":"C-Legend"}
    ]
  },
  "flows": {
    "lanes": ["Operator UI","Render Engine","KPI Logic","System Status","Logger"],
    "items": [
      {"id":"UF-01","name":"Saturation SA","steps":[
        {"lane":"Operator UI","text":"Check Z1 cues","out":"Baseline LOD"},
        {"lane":"Render Engine","text":"Compute density","out":"LOD level"},
        {"lane":"Operator UI","text":"Toggle FOV if needed","out":"Layer state"},
        {"lane":"KPI Logic","text":"Update TSA estimate","out":"KPI refresh"}
      ]},
      {"id":"EF-01","name":"Threshold & Rollback","steps":[
        {"lane":"System Status","text":"Detect lag>500ms or FPS<30 (3s)","out":"Alert badge"},
        {"lane":"Render Engine","text":"Auto rollback to 2D if 5s persists","out":"rollback=2D"},
        {"lane":"Logger","text":"Record reason/owner/time","out":"audit_log"}
      ]}
    ],
    "decisions":[
      {"id":"D-01","cond":"FPS >= 30 ?","yes":"Keep LOD","no":"Increase LOD"},
      {"id":"D-02","cond":"lag_ms <= 500 ?","yes":"Normal","no":"Warn / EF-01"}
    ]
  }
}

# ----------------------------
# Controls (zoom/height per section)
# ----------------------------
with st.sidebar:
    st.header("Viewport Controls")
    ia_zoom = st.slider("IA Zoom (%)", 50, 250, 100, 5)
    ia_h = st.slider("IA Viewport Height (px)", 400, 1200, 700, 50)
    fl_zoom = st.slider("Flow Zoom (%)", 50, 250, 100, 5)
    fl_h = st.slider("Flow Viewport Height (px)", 400, 1200, 700, 50)
    dc_zoom = st.slider("Decision Zoom (%)", 50, 250, 100, 5)
    dc_h = st.slider("Decision Viewport Height (px)", 300, 1000, 500, 50)

# ----------------------------
# Renderers
# ----------------------------
def render_ia(spec:Dict[str,Any]) -> Tuple[str, int, int]:
    ia = spec.get("ia", {})
    zones = ia.get("zones", [])
    comps = ia.get("components", [])
    scope_lines = ia.get("scope", [])
    canv = spec.get("canvas", {})
    W = int(canv.get("width", 1600)); H = int(canv.get("height", 900))
    svg = [svg_header(W, H), rect(0,0,W,H,0,0,fill=spec.get("canvas",{}).get("theme",{}).get("bg","#FAFAFA"), stroke="#EEE", sw=0.5)]
    title = spec.get("project",{}).get("title","IA Diagram")
    svg.append(text(32, 44, title, size=24, weight="600"))
    svg.append(rect(28, 60, W-56, 70, rx=10, ry=10, fill="#FFFFFF", stroke="#D0D6E0"))
    scope_txt = "  •  ".join(scope_lines)
    svg.append(text(40, 96, "Scope: " + scope_txt, size=14, fill="#333"))
    svg.append(text(32, 150, "Screen Zoning", size=18, weight="600"))
    for z in zones:
        zx,zy,zw,zh = int(z.get("x",0)), int(z.get("y",0)), int(z.get("w",100)), int(z.get("h",80))
        fill = z.get("fill", "#F3F7FF")
        svg.append(rect(zx,zy,zw,zh,rx=12,ry=12,fill=fill,stroke="#B8C2D6"))
        svg.append(text(zx+10, zy+26, f"{z['id']} - {z.get('label','')}", size=14, weight="600"))
    svg.append(text(W-420, 150, "Components (by Zone)", size=18, weight="600"))
    y = 180
    for c in comps:
        svg.append(rect(W-440, y-18, 392, 36, rx=10, ry=10, fill="#FFFFFF", stroke="#E3E7EF"))
        svg.append(text(W-430, y+4, f"[{c.get('zone','?')}] {c.get('title','')}", size=13, fill="#222"))
        y += 44
    svg.append(svg_footer())
    return "".join(svg), W, H

def render_flow_item(spec:Dict[str,Any], item:Dict[str,Any], y_offset:int, W:int) -> Tuple[str,int]:
    lanes: List[str] = spec.get("flows",{}).get("lanes",["Flow"])
    lane_h = 100
    lane_gap = 10
    svg=[]; lane_y={}
    for i,l in enumerate(lanes):
        y = y_offset + i*(lane_h+lane_gap)
        lane_y[l]=y
        svg.append(rect(28, y, W-56, lane_h, rx=12, ry=12, fill="#FBFCFF", stroke="#E1E6F0"))
        svg.append(text(40, y+24, l, size=14, fill="#4A5568", weight="600"))
    steps: List[Dict[str,Any]] = item.get("steps",[])
    cols = max(3, len(steps))
    col_w = (W-180)/cols
    nodes=[]
    for idx, s in enumerate(steps):
        lane = s.get("lane", lanes[min(idx,len(lanes)-1)])
        y = lane_y.get(lane, y_offset) + lane_h/2
        x = 100 + col_w*(idx+0.5)
        svg.append(rect(x-120, y-26, 240, 52, rx=12, ry=12, fill="#FFFFFF", stroke="#A0AEC0"))
        lines = wrap_lines(s.get("text",""), 28)
        for j,ln in enumerate(lines[:2]):
            svg.append(text(x, y-6+16*j, ln, anchor="middle", size=14))
        out = s.get("out","")
        if out:
            svg.append(text(x, y+28, f"-> {out}", anchor="middle", size=12, fill="#555"))
        nodes.append((x,y))
        if idx>0:
            px,py = nodes[idx-1]
            svg.append(arrow(px+120, py, x-120, y, "#6B7280"))
    svg.insert(0, text(32, y_offset-12, f"{item.get('id','FLOW')} - {item.get('name','')}", size=18, weight="700"))
    return "".join(svg), y_offset + len(lanes)*(lane_h+lane_gap) + 50

def render_flows(spec:Dict[str,Any]) -> Tuple[str,int,int]:
    canv = spec.get("canvas", {})
    W = int(canv.get("width",1600)); H = int(canv.get("height",900))
    items: List[Dict[str,Any]] = spec.get("flows",{}).get("items",[])
    svg=[svg_header(W, H), rect(0,0,W,H,0,0,fill=spec.get("canvas",{}).get("theme",{}).get("bg","#FAFAFA"), stroke="#EEE", sw=0.5)]
    y = 70
    svg.append(text(32, 40, "Flows (Swimlanes)", size=22, weight="600"))
    for it in items:
        block, y = render_flow_item(spec, it, y+30, W)
        svg.append(block)
        y += 20
    svg.append(svg_footer())
    return "".join(svg), W, max(H, y+60)

def render_decisions(spec:Dict[str,Any]) -> Tuple[str,int,int]:
    decs = spec.get("flows",{}).get("decisions",[])
    canv = spec.get("canvas", {}); W = int(canv.get("width",1600))
    rows = max(1, len(decs))
    H = 140 + rows*110
    svg=[svg_header(W, H), rect(0,0,W,H,0,0,fill=spec.get("canvas",{}).get("theme",{}).get("bg","#FAFAFA"), stroke="#EEE", sw=0.5)]
    svg.append(text(32, 40, "Decision Points", size=22, weight="600"))
    for i,d in enumerate(decs):
        y = 110 + i*110
        cx = 260
        svg.append(diamond(cx, y, 200, 80))
        svg.append(text(cx, y-8, d.get("id","D-?"), anchor="middle", size=14, weight="700"))
        svg.append(text(cx, y+18, d.get("cond",""), anchor="middle", size=12))
        svg.append(rect(cx+260, y-26, 300, 52, rx=12, ry=12, fill="#EFFFF5", stroke="#49A36B"))
        svg.append(text(cx+410, y+6, d.get("yes",""), anchor="middle", size=13))
        svg.append(arrow(cx+100, y, cx+260, y, "#4A9"))
        svg.append(rect(cx-560, y-26, 300, 52, rx=12, ry=12, fill="#FFF5F5", stroke="#CC6666"))
        svg.append(text(cx-410, y+6, d.get("no",""), anchor="middle", size=13))
        svg.append(arrow(cx-100, y, cx-260, y, "#C66"))
    svg.append(svg_footer())
    return "".join(svg), W, H

def show_svg(svg_text:str, width:int, height:int, zoom:int, viewport_h:int, key:str):
    scale = zoom / 100.0
    # Outer scrollable box (full width), inner scaled canvas
    html = f'''
    <div style="width:100%; border:1px solid #e3e3e3; border-radius:10px; background:#fff; overflow:auto; height:{viewport_h}px;">
      <div style="transform: scale({scale}); transform-origin: top left; width:{width}px; height:{height}px;">
        {svg_text}
      </div>
    </div>
    '''
    st_html(html, height=viewport_h+20)

# ----------------------------
# Render sections with controls
# ----------------------------
spec = default_spec  # could add JSON input later if needed

st.markdown("### IA Diagram (PPT style)")
svg_ia, W_ia, H_ia = render_ia(spec)
show_svg(svg_ia, W_ia, H_ia, ia_zoom, ia_h, key="ia")

st.markdown("### Flow Diagram (PPT style, Swimlanes)")
svg_flow, W_fl, H_fl = render_flows(spec)
show_svg(svg_flow, W_fl, H_fl, fl_zoom, fl_h, key="flow")

st.markdown("### Decision Points (Yes/No)")
svg_dec, W_dc, H_dc = render_decisions(spec)
show_svg(svg_dec, W_dc, H_dc, dc_zoom, dc_h, key="dec")
