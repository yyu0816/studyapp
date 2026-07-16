import streamlit as st

def get_contrast_color(hex_color: str) -> str:
    """Calculate contrasting text color (white/black) based on background hex color."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        try:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return "#ffffff" if luminance < 0.5 else "#222222"
        except:
            pass
    return "#222222"

def render_timeline(events: list[dict], title: str = "### 🕒 時間軸") -> None:
    # ── Timeline ──────────────────────────────────────────────────────────────
    HOUR_PX = 60          # pixels per hour on the timeline
    TIMELINE_START = 0    # start at 00:00
    TIMELINE_END   = 24   # end at 24:00
    TOTAL_PX = HOUR_PX * (TIMELINE_END - TIMELINE_START)

    def event_to_px(start_str: str, end_str: str):
        try:
            sh, sm = start_str.split(":")
            eh, em = end_str.split(":")
            top    = int(sh) * HOUR_PX + int(sm) * HOUR_PX / 60
            bottom = int(eh) * HOUR_PX + int(em) * HOUR_PX / 60
            if bottom <= top:
                bottom = top + HOUR_PX   # at least 1 hour if end <= start
            return top, bottom
        except Exception:
            return 0, HOUR_PX

    # Assign column index for overlapping events (simple greedy)
    def assign_columns(events_to_assign):
        slots: list[list] = []     # each slot is a list of (top, bottom, event_idx)
        result = {}                # event_idx -> (col, n_cols_in_group)
        for i, ev in enumerate(events_to_assign):
            top, bottom = event_to_px(ev.get("start", "00:00"), ev.get("end", "01:00"))
            placed = False
            for col_idx, slot in enumerate(slots):
                last_top, last_bottom, _ = slot[-1]
                if top >= last_bottom:
                    slot.append((top, bottom, i))
                    result[i] = col_idx
                    placed = True
                    break
            if not placed:
                slots.append([(top, bottom, i)])
                result[i] = len(slots) - 1

        # Determine how many columns each event needs to share
        final = {}
        for i, ev in enumerate(events_to_assign):
            top, bottom = event_to_px(ev.get("start", "00:00"), ev.get("end", "01:00"))
            concurrent = sum(
                1 for j, ev2 in enumerate(events_to_assign)
                if j != i and event_to_px(ev2.get("start", "00:00"), ev2.get("end", "01:00"))[0] < bottom
                and event_to_px(ev2.get("start", "00:00"), ev2.get("end", "01:00"))[1] > top
            )
            final[i] = (result[i], concurrent + 1)
        return final

    # Only events that actually appear on the timeline (not all-day)
    timeline_events = [e for e in events if not e.get("is_all_day")]
    event_layout = assign_columns(timeline_events)

    if title:
        st.markdown(title)

    # Build HTML timeline with absolute positioning
    # Outer wrapper: fixed height with relative positioning
    timeline_html = (
        f"<div style='position:relative; height:{TOTAL_PX}px; "
        f"margin-left:60px; border-left:3px solid #4f84ff; "
        f"margin-top:10px; margin-bottom:20px;'>"
    )

    # Hour tick marks (removed white line)
    for hour in range(TIMELINE_START, TIMELINE_END + 1):
        top_px = (hour - TIMELINE_START) * HOUR_PX
        hour_label = f"{hour:02d}:00" if hour < 24 else ""
        timeline_html += (
            f"<div style='position:absolute; top:{top_px}px; left:0; right:0;'>"
            f"<span style='position:absolute; left:-72px; top:-10px; "
            f"width:60px; text-align:right; color:#aaa; font-size:12px; "
            f"line-height:1;'>{hour_label}</span>"
            f"<div style='position:absolute; left:-6px; top:-4px; width:8px; height:8px; "
            f"border-radius:50%; background:#4f84ff;'></div>"
            f"</div>"
        )

    # Event cards — absolutely positioned, split into columns if overlapping
    CARD_LEFT_OFFSET = 10   # px from the timeline line
    CARD_WIDTH_BASE  = 160  # px total card area for one column

    for i, event in enumerate(timeline_events):
        col_idx, n_cols = event_layout.get(i, (0, 1))
        top_px, bottom_px = event_to_px(
            event.get("start", "00:00"), event.get("end", "01:00")
        )
        height_px = max(bottom_px - top_px, 24)

        emoji = event.get("emoji", "📌")
        color = event.get("display_color", event.get("color", "#4f84ff"))
        text_color = get_contrast_color(color)
        title_str = event.get("title", "未命名行程")
        start = event.get("start", "")
        end   = event.get("end", "")
        
        # Additional text for study targets etc.
        subtitle = event.get("subtitle", "")
        subtitle_html = f"<div style='margin-top:2px; font-size:11px; font-weight:bold; color:{text_color};'>{subtitle}</div>" if subtitle else ""

        card_width  = CARD_WIDTH_BASE // n_cols
        card_left   = CARD_LEFT_OFFSET + col_idx * card_width

        timeline_html += (
            f"<div style='position:absolute; top:{top_px}px; height:{height_px}px; "
            f"left:{card_left}px; width:{card_width - 4}px; "
            f"background:{color}; "
            f"border-radius:6px; padding:4px 6px; overflow:hidden; box-sizing:border-box; "
            f"font-size:12px; line-height:1.3; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>"
            f"<strong style='color:{text_color};'>{emoji}</strong> "
            f"<span style='color:{text_color}; font-weight: 500;'>{title_str}</span><br>"
            f"<span style='color:{text_color}; font-size:11px; opacity:0.8;'>{start}–{end}</span>"
            f"{subtitle_html}"
            f"</div>"
        )

    timeline_html += "</div>"

    if hasattr(st, "html"):
        st.html(timeline_html)
    else:
        st.markdown(timeline_html, unsafe_allow_html=True)
