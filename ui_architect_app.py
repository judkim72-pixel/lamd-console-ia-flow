
import json, math
import streamlit as st
from typing import Dict, List, Any, Tuple
from streamlit.components.v1 import html as st_html

st.set_page_config(page_title="UI Architect — IA/Flow v3 (no cropping)", layout="wide")
st.title("UI Architect — IA/Flow v3")
st.caption("Fix: no internal SVG cropping (extra margins + translated content).")

# ---------- helpers ----------
def svg_skeleton(w:int, h:int, inner:str, margin:int=120, bg="#FAFAFC") -> str:
    # Expand outer canvas by margin on four sides, and translate inner group.
    W = w + margin*2
    H = h + margin*2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="{bg}" />'
        f'<g transform="translate({margin},{margin})">'
        f'{inner}'
        f'</g></svg>'
    )

def rect(x,y,w,h,rx=12,ry=12,fill="#FFFFFF",stroke="#222",sw=1.4) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def text(x,y,s,anchor="start",size=14,fill="#111",weight="400") -> str:
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}" font-family="Segoe UI, Arial, Helvetica">{s}</text>'
def line(x1,y1,x2,y2,stroke="#999",sw=1.2) -> str:
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"/>'
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
def wrap_lines(s:str, max_chars:int=28):
    words = s.split(); lines=[]; cur=""
    for w in words:
        if len(cur)+len(w)+1 <= max_chars:
            cur=(cur+" "+w).strip()
        else:
            lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines or [""]

# ---------- default spec ----------
spec = {
  "project": {"title": "LAMD Left Panel - IA & Flows"},
  "canvas": {"width": 1600, "height": 900, "theme": {"bg":"#FAFAFC"}},
  "ia": {
    "scope": ["Left Graphic Panel Only", "27\" FHD (1920x1080)", "Avoid red alerts"],
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

# ---------- controls ----------
with st.sidebar:
    st.header("Viewport")
    zoom = st.slider("Zoom (%)", 50, 250, 100, 5)
    height = st.slider("Viewport Height (px)", 400, 1400, 800, 50)

# ---------- IA renderer ----------
def render_ia(s:Dict[str,Any]) -> Tuple[str,int,int]:
    canv = s.get("canvas", {})
    W = int(canv.get("width",1600)); H = int(canv.get("height",900))
    ia = s.get("ia", {}); zones = ia.get("zones", []); comps = ia.get("components", [])
    scope = ia.get("scope", [])
    g = []
    g.append(text(32, 36, s.get("project",{}).get("title","IA"), size=24, weight="600"))
    g.append(rect(28, 48, W-56, 70, rx=10, ry=10, fill="#FFFFFF", stroke="#D0D6E0"))
    g.append(text(40, 90, "Scope: " + " | ".join(scope), size=14))
    g.append(text(32, 140, "Screen Zoning", size=18, weight="600"))
    for z in zones:
        g.append(rect(z["x"], z["y"], z["w"], z["h"], rx=12, ry=12, fill=z.get("fill","#F3F7FF"), stroke="#B8C2D6"))
        g.append(text(z["x"]+10, z["y"]+26, f'{z["id"]} - {z["label"]}', size=14, weight="600"))
    # components legend right
    x_leg = W-420; y=160
    g.append(text(x_leg, 140, "Components (by Zone)", size=18, weight="600"))
    for c in comps:
        g.append(rect(x_leg-20, y-18, 392, 36, rx=10, ry=10, fill="#FFFFFF", stroke="#E3E7EF"))
        g.append(text(x_leg-10, y+4, f'[{c["zone"]}] {c["title"]}', size=13))
        y += 44
    inner = "".join(g)
    svg = svg_skeleton(W, H, inner, margin=160, bg=canv.get("theme",{}).get("bg","#FAFAFC"))
    return svg, W+320, H+320

# ---------- Flow renderer ----------
def render_flows(s:Dict[str,Any]) -> Tuple[str,int,int]:
    canv = s.get("canvas", {})
    W = int(canv.get("width",1600)); baseH = int(canv.get("height",900))
    lanes = s.get("flows",{}).get("lanes",["Flow"])
    items = s.get("flows",{}).get("items",[])

    lane_h=110; lane_gap=12
    y = 70
    g=[text(32, 40, "Flows (Swimlanes)", size=22, weight="600")]
    for it in items:
        g.append(text(32, y-12, f'{it.get("id","FLOW")} - {it.get("name","")}', size=18, weight="700"))
        lane_y={}
        for i,l in enumerate(lanes):
            yy = y + i*(lane_h+lane_gap); lane_y[l]=yy
            g.append(rect(28, yy, W-56, lane_h, rx=12, ry=12, fill="#FBFCFF", stroke="#E1E6F0"))
            g.append(text(40, yy+24, l, size=14, weight="600"))
        steps = it.get("steps",[]); cols=max(3, len(steps)); col_w=(W-180)/cols; nodes=[]
        for idx, stp in enumerate(steps):
            lane = stp.get("lane", lanes[min(idx,len(lanes)-1)])
            cy = lane_y[lane] + lane_h/2
            cx = 100 + col_w*(idx+0.5)
            g.append(rect(cx-120, cy-26, 240, 52, rx=12, ry=12, fill="#FFFFFF", stroke="#A0AEC0"))
            for j,ln in enumerate(wrap_lines(stp.get("text",""), 28)[:2]):
                g.append(text(cx, cy-6+16*j, ln, anchor="middle", size=14))
            if stp.get("out"): g.append(text(cx, cy+28, "-> "+stp["out"], anchor="middle", size=12))
            if nodes:
                px,py=nodes[-1]; g.append(arrow(px+120, py, cx-120, cy, "#6B7280"))
            nodes.append((cx,cy))
        y = y + len(lanes)*(lane_h+lane_gap) + 60
    H = max(baseH, y+40)
    inner = "".join(g)
    svg = svg_skeleton(W, H, inner, margin=160, bg=canv.get("theme",{}).get("bg","#FAFAFC"))
    return svg, W+320, H+320

# ---------- Decisions ----------
def render_decisions(s:Dict[str,Any]) -> Tuple[str,int,int]:
    canv = s.get("canvas", {}); W = int(canv.get("width",1600))
    decs = s.get("flows",{}).get("decisions",[])
    rows=max(1,len(decs)); H=140+rows*120
    g=[text(32, 40, "Decision Points", size=22, weight="600")]
    for i,d in enumerate(decs):
        y = 120 + i*120; cx=280
        g.append(diamond(cx, y, 200, 80))
        g.append(text(cx, y-8, d.get("id","D-?"), anchor="middle", size=14, weight="700"))
        g.append(text(cx, y+18, d.get("cond",""), anchor="middle", size=12))
        g.append(rect(cx+300, y-26, 320, 52, rx=12, ry=12, fill="#EFFFF5", stroke="#49A36B"))
        g.append(text(cx+460, y+6, d.get("yes",""), anchor="middle", size=13))
        g.append(arrow(cx+100, y, cx+300, y, "#4A9"))
        g.append(rect(cx-620, y-26, 320, 52, rx=12, ry=12, fill="#FFF5F5", stroke="#CC6666"))
        g.append(text(cx-460, y+6, d.get("no",""), anchor="middle", size=13))
        g.append(arrow(cx-100, y, cx-300, y, "#C66"))
    inner="".join(g)
    svg = svg_skeleton(W, H, inner, margin=160, bg=canv.get("theme",{}).get("bg","#FAFAFC"))
    return svg, W+320, H+320

# ---------- view ----------
def viewport(svg_text:str, w:int, h:int, zoom:int, height:int):
    scale = zoom/100.0
    html = f'''
    <div style="width:100%; border:1px solid #e3e3e3; border-radius:10px; background:#fff; overflow:auto; height:{height}px;">
      <div style="transform: scale({scale}); transform-origin: top left; width:{w}px; height:{h}px;">
        {svg_text}
      </div>
    </div>'''
    st_html(html, height=height+20)

st.markdown("### IA Diagram")
svg_ia, w1, h1 = render_ia(spec)
viewport(svg_ia, w1, h1, zoom, height)

st.markdown("### Flow Diagram")
svg_fl, w2, h2 = render_flows(spec)
viewport(svg_fl, w2, h2, zoom, height)

st.markdown("### Decision Points")
svg_dc, w3, h3 = render_decisions(spec)
viewport(svg_dc, w3, h3, zoom, height)
