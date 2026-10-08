import os
import xml.etree.ElementTree as ET
from core.config import ACTIONS_FILE, IMG_DIR

def parse_xml_actions(file_path):
    actions = {}
    if not os.path.exists(file_path):
        return actions
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for action in root.findall("Action"):
            name = action.find("Name").text if action.find("Name") is not None else ""
            frames = []
            anim = action.find("Animation")
            if anim is not None:
                for frame in anim.findall("Frame"):
                    img = frame.find("Image")
                    if img is not None and img.text:
                        frames.append(img.text)
            if name:
                actions[name] = frames
    except Exception:
        pass
    return actions

XML_ACTIONS = parse_xml_actions(ACTIONS_FILE)

# Detect whether current skin uses standard Shimeji numbered frames (shime1.png - shime46.png)
is_standard_shimeji = os.path.exists(os.path.join(IMG_DIR, "shime1.png"))

if is_standard_shimeji:
    STAND_FRAMES   = ["shime1"]
    WALK_FRAMES    = ["shime1", "shime2", "shime3", "shime2"]
    WALK_BACK      = ["shime2", "shime3"]
    SIT_FRAMES     = ["shime11"]
    GUITAR_FRAMES  = ["shime18", "shime19", "shime20", "shime21"]
    LIE_FRAMES     = ["shime11"]
    BLOB_FRAMES    = ["shime26", "shime27", "shime28", "shime29"]
    GHOST_FRAMES   = ["shime30", "shime31", "shime32", "shime33"]
    BOX_FRAMES     = ["shime34", "shime35", "shime36", "shime37"]
    FALL_FRAMES    = ["shime4"]
    KNEEL_FRAMES   = ["shime11"]
    CARRY_FRAMES   = ["shime5", "shime6", "shime7"]
    DEPRESS_FRAMES = ["shime8", "shime9", "shime10"]
    AWAY_FRAMES    = ["shime38", "shime39", "shime40", "shime41"]
    CLIMB_FRAMES   = ["shime12", "shime13", "shime14"]
else:
    STAND_FRAMES   = XML_ACTIONS.get("Stay", ["stand1", "stand2"])
    WALK_FRAMES    = XML_ACTIONS.get("WalkRight", ["walk1", "walk2", "walk3", "walk4", "walk5"])
    WALK_BACK      = XML_ACTIONS.get("WalkBack", ["walk_back1", "walk_back2"])
    SIT_FRAMES     = XML_ACTIONS.get("Sit", ["sit1", "sit2", "sit3", "sit4", "sit5", "sit6"])
    GUITAR_FRAMES  = XML_ACTIONS.get("Guitar", ["guitar1", "guitar2", "guitar3"])
    LIE_FRAMES     = XML_ACTIONS.get("LieDown", ["lie1", "lie2", "lie3"])
    BLOB_FRAMES    = XML_ACTIONS.get("Blob", ["blob1", "blob2", "blob3", "blob4", "blob5", "blob6", "blob7"])
    GHOST_FRAMES   = XML_ACTIONS.get("Ghost", ["ghost1", "ghost2", "ghost3"])
    BOX_FRAMES     = XML_ACTIONS.get("BoxTrick", ["box1", "box2", "box3", "smoke1", "stand1"])
    FALL_FRAMES    = XML_ACTIONS.get("Fall", ["fall1"])
    KNEEL_FRAMES   = XML_ACTIONS.get("Kneel", ["kneel1"])
    CARRY_FRAMES   = STAND_FRAMES
    DEPRESS_FRAMES = STAND_FRAMES
    AWAY_FRAMES    = STAND_FRAMES
    CLIMB_FRAMES   = WALK_FRAMES

ALL_REQUIRED_FRAMES = set(
    STAND_FRAMES + WALK_FRAMES + WALK_BACK + SIT_FRAMES +
    GUITAR_FRAMES + LIE_FRAMES + BLOB_FRAMES + GHOST_FRAMES +
    BOX_FRAMES + FALL_FRAMES + KNEEL_FRAMES + CARRY_FRAMES +
    DEPRESS_FRAMES + AWAY_FRAMES + CLIMB_FRAMES
)
