
import json, math, io, os
import streamlit as st
from typing import Dict, List, Any, Tuple

st.set_page_config(page_title="UI Architect — PPT-style IA & Flow", layout="wide")
st.title("UI Architect — PPT-style IA & Flow (PPT style diagrams)")
st.caption("JSON spec -> PPT-style IA/Flow/Decision as SVG. (ASCII-only to avoid Unicode issues)")

# ----------------------------
# SVG helpers (no external deps)
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
# Default sample spec (ASCII-safe)
# ----------------------------
default_spec = {
  "project": {"title": "LAMD Left Panel - IA & Flows", "author": "AEON Communications", "version": "v1.0"},
  "canvas": {"width": 1280, "height": 720, "theme": {"bg":"#FAFAFC","ink":"#111","accent":"#2B6CB0","muted":"#999"}},
  "ia": {
    "scope": ["Left Graphic Panel Only", "27\" FHD (1920x1080)", "Avoid red alerts", "Security labels required"],
    "zones": [
      {"id": "Z5", "label": "System Status", "x": 40, "y": 80, "w": 1200, "h": 40, "fill":"#FFF7F0"},
      {"id": "Z2", "label": "Layer Controls", "x": 40, "y": 130, "w": 180, "h": 500, "fill":"#F3F7FF"},
      {"id": "Z3", "label": "KPI Mini-View", "x": 230, "y": 130, "w": 240, "h": 120, "fill":"#FFFDE7"},
      {"id": "Z4", "label": "Legend & Scale", "x": 230, "y": 590, "w": 1010, "h": 40, "fill":"#EEF9FF"},
      {"id": "Z1", "label": "Main Canvas", "x": 230, "y": 260, "w": 1010, "h": 320, "fill":"#EEF5EE"}
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

# ----------------------------------------
# Inputs: JSON spec (paste or upload)
# ----------------------------------------
left, right = st.columns([0.48, 0.52], gap="large")

with left:
    st.subheader("1) Spec Input")
    mode = st.radio("Input Mode", ["Use Sample", "Paste JSON", "Upload JSON"], horizontal=True)
    spec: Dict[str, Any] = {}
    if mode == "Use Sample":
        spec = default_spec
        st.code(json.dumps(spec, indent=2), language="json")
    elif mode == "Paste JSON":
        txt = st.text_area("JSON Spec", value=json.dumps(default_spec, indent=2), height=320)
        try:
            spec = json.loads(txt)
        except Exception as e:
            st.error(f"JSON parse error: {e}")
    else:
        up = st.file_uploader("Upload JSON", type=["json"])
        if up:
            try:
                spec = json.loads(up.read().decode("utf-8"))
                st.success("JSON loaded")
            except Exception as e:
                st.error(f"Parse error: {e}")
        else:
            st.info("Upload a JSON file.")

with right:
    st.subheader("2) Output Canvas")
    canv = spec.get("canvas", {})
    W = int(canv.get("width", 1280)); H = int(canv.get("height", 720))
    theme = canv.get("theme", {"bg":"#FAFAFC","ink":"#111","accent":"#2B6CB0","muted":"#999"})
    st.write(f"Canvas: {W}x{H}")
    st.write("Theme:", theme)

# ----------------------------------------
# Helpers
# ----------------------------------------
from streamlit.components.v1 import html as st_html

def render_ia(spec:Dict[str,Any]) -> str:
    ia = spec.get("ia", {})
    zones = ia.get("zones", [])
    comps = ia.get("components", [])
    scope_lines = ia.get("scope", [])
    canv = spec.get("canvas", {})
    W = int(canv.get("width", 1280)); H = int(canv.get("height", 720))
    svg = [svg_header(W, H), rect(0,0,W,H,0,0,fill=spec.get("canvas",{}).get("theme",{}).get("bg","#FAFAFA"), stroke="#EEE", sw=0.5)]
    title = spec.get("project",{}).get("title","IA Diagram")
    svg.append(text(32, 44, title, size=22, weight="600"))
    svg.append(rect(28, 60, W-56, 60, rx=8, ry=8, fill="#FFFFFF", stroke="#D0D6E0"))
    scope_txt = "  •  ".join(scope_lines)
    svg.append(text(40, 90, "Scope: " + scope_txt, size=14, fill="#333"))
    svg.append(text(32, 140, "Screen Zoning", size=16, weight="600"))
    for z in zones:
        zx,zy,zw,zh = int(z.get("x",0)), int(z.get("y",0)), int(z.get("w",100)), int(z.get("h",80))
        fill = z.get("fill", "#F3F7FF")
        svg.append(rect(zx,zy,zw,zh,rx=10,ry=10,fill=fill,stroke="#B8C2D6"))
        svg.append(text(zx+10, zy+24, f"{z['id']}  -  {z.get('label','')}", size=14, weight="600"))
    svg.append(text(W-360, 140, "Components (by Zone)", size=16, weight="600"))
    y = 170
    for c in comps:
        svg.append(rect(W-380, y-18, 352, 36, rx=8, ry=8, fill="#FFFFFF", stroke="#E3E7EF"))
        svg.append(text(W-370, y+4, f"[{c.get('zone','?')}] {c.get('title','')}", size=13, fill="#222"))
        y += 44
    svg.append(svg_footer())
    return "".join(svg)

def render_flow_item(spec:Dict[str,Any], item:Dict[str,Any], y_offset:int) -> Tuple[str,int]:
    lanes: List[str] = spec.get("flows",{}).get("lanes",["Flow"])
    lane_h = 90
    lane_gap = 8
    canv = spec.get("canvas", {}); W = int(canv.get("width",1280))
    svg=[]; lane_y={}
    for i,l in enumerate(lanes):
        y = y_offset + i*(lane_h+lane_gap)
        lane_y[l]=y
        svg.append(rect(28, y, W-56, lane_h, rx=10, ry=10, fill="#FBFCFF", stroke="#E1E6F0"))
        svg.append(text(40, y+22, l, size=13, fill="#4A5568", weight="600"))
    steps: List[Dict[str,Any]] = item.get("steps",[])
    cols = max(3, len(steps))
    col_w = (W-180)/cols
    nodes=[]
    for idx, s in enumerate(steps):
        lane = s.get("lane", lanes[min(idx,len(lanes)-1)])
        y = lane_y.get(lane, y_offset) + lane_h/2
        x = 100 + col_w*(idx+0.5)
        svg.append(rect(x-110, y-24, 220, 48, rx=10, ry=10, fill="#FFFFFF", stroke="#A0AEC0"))
        lines = wrap_lines(s.get("text",""), 26)
        for j,ln in enumerate(lines[:2]):
            svg.append(text(x, y-6+14*j, ln, anchor="middle", size=13))
        out = s.get("out","")
        if out:
            svg.append(text(x, y+26, f"-> {out}", anchor="middle", size=11, fill="#555"))
        nodes.append((x,y))
        if idx>0:
            px,py = nodes[idx-1]
            svg.append(arrow(px+110, py, x-110, y, "#6B7280"))
    svg.insert(0, text(32, y_offset-10, f"{item.get('id','FLOW')} - {item.get('name','')}", size=16, weight="700"))
    return "".join(svg), y_offset + len(lanes)*(lane_h+lane_gap) + 40

def render_flows(spec:Dict[str,Any]) -> str:
    canv = spec.get("canvas", {})
    W = int(canv.get("width",1280)); H = int(canv.get("height",720))
    items: List[Dict[str,Any]] = spec.get("flows",{}).get("items",[])
    svg=[svg_header(W, H), rect(0,0,W,H,0,0,fill=spec.get("canvas",{}).get("theme",{}).get("bg","#FAFAFA"), stroke="#EEE", sw=0.5)]
    y = 60
    svg.append(text(32, 36, "Flows (Swimlanes)", size=22, weight="600"))
    for it in items:
        block, y = render_flow_item(spec, it, y+30)
        svg.append(block)
        y += 20
    svg.append(svg_footer())
    return "".join(svg)

def render_decisions(spec:Dict[str,Any]) -> str:
    decs = spec.get("flows",{}).get("decisions",[])
    canv = spec.get("canvas", {}); W = int(canv.get("width",1280))
    rows = max(1, len(decs))
    H = 120 + rows*90
    svg=[svg_header(W, H), rect(0,0,W,H,0,0,fill=spec.get("canvas",{}).get("theme",{}).get("bg","#FAFAFA"), stroke="#EEE", sw=0.5)]
    svg.append(text(32, 36, "Decision Points", size=22, weight="600"))
    for i,d in enumerate(decs):
        y = 90 + i*90
        cx = 200
        svg.append(diamond(cx, y, 180, 70))
        svg.append(text(cx, y-6, d.get("id","D-?"), anchor="middle", size=14, weight="700"))
        svg.append(text(cx, y+16, d.get("cond",""), anchor="middle", size=12))
        svg.append(rect(cx+200, y-22, 260, 44, rx=10, ry=10, fill="#EFFFF5", stroke="#49A36B"))
        svg.append(text(cx+330, y+4, d.get("yes",""), anchor="middle", size=12))
        svg.append(arrow(cx+90, y, cx+200, y, "#4A9"))
        svg.append(rect(cx-460, y-22, 260, 44, rx=10, ry=10, fill="#FFF5F5", stroke="#CC6666"))
        svg.append(text(cx-330, y+4, d.get("no",""), anchor="middle", size=12))
        svg.append(arrow(cx-90, y, cx-200, y, "#C66"))
    svg.append(svg_footer())
    return "".join(svg)

# ----------------------------
# Render
# ----------------------------
st.markdown("---")
st.header("IA Diagram (PPT style)")
svg_ia = render_ia(default_spec if 'spec' not in locals() or not spec else spec)
st_html(f'<div style="border:1px solid #e3e3e3;border-radius:10px;overflow:auto;height:560px">{svg_ia}</div>', height=580)
st.download_button("Download IA SVG", data=svg_ia.encode("utf-8"), file_name="ia_diagram.svg", mime="image/svg+xml")

st.markdown("---")
st.header("Flow Diagram (PPT style, Swimlanes)")
svg_flow = render_flows(default_spec if 'spec' not in locals() or not spec else spec)
st_html(f'<div style="border:1px solid #e3e3e3;border-radius:10px;overflow:auto;height:560px">{svg_flow}</div>', height=580)
st.download_button("Download Flows SVG", data=svg_flow.encode("utf-8"), file_name="flows_diagram.svg", mime="image/svg+xml")

st.markdown("---")
st.header("Decision Points (Yes/No)")
svg_dec = render_decisions(default_spec if 'spec' not in locals() or not spec else spec)
st_html(f'<div style="border:1px solid #e3e3e3;border-radius:10px;overflow:auto;height:420px">{svg_dec}</div>', height=440)
st.download_button("Download Decisions SVG", data=svg_dec.encode("utf-8"), file_name="decisions.svg", mime="image/svg+xml")

st.markdown("---")
st.caption("ASCII-only app file to avoid Unicode parser issues on some environments.")
