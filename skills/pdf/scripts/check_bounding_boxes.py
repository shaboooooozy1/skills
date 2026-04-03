from dataclasses import dataclass
import json
import sys


# Script to check that the `fields.json` file that Claude creates when analyzing PDFs
# does not have overlapping bounding boxes. See forms.md.


@dataclass
class RectAndField:
    rect: list[float]
    rect_type: str
    field: dict


# Returns a list of messages that are printed to stdout for Claude to read.
def get_bounding_box_messages(fields_json_stream) -> list[str]:
    messages = []
    fields = json.load(fields_json_stream)
    messages.append(f"Read {len(fields['form_fields'])} fields")

    def rects_intersect(rect1, rect2):
        disjoint_horizontal = rect1[0] >= rect2[2] or rect1[2] <= rect2[0]
        disjoint_vertical = rect1[1] >= rect2[3] or rect1[3] <= rect2[1]
        return not (disjoint_horizontal or disjoint_vertical)

    rects_and_fields = []
    for field in fields["form_fields"]:
        rects_and_fields.append(RectAndField(field["label_bounding_box"], "label", field))
        rects_and_fields.append(RectAndField(field["entry_bounding_box"], "entry", field))

    has_error = False
    for i, current_item in enumerate(rects_and_fields):
        # This is O(N^2); we can optimize if it becomes a problem.
        for j in range(i + 1, len(rects_and_fields)):
            other_item = rects_and_fields[j]
            if current_item.field["page_number"] == other_item.field["page_number"] and rects_intersect(current_item.rect, other_item.rect):
                has_error = True
                if current_item.field is other_item.field:
                    messages.append(f"FAILURE: intersection between label and entry bounding boxes for `{current_item.field['description']}` ({current_item.rect}, {other_item.rect})")
                else:
                    messages.append(f"FAILURE: intersection between {current_item.rect_type} bounding box for `{current_item.field['description']}` ({current_item.rect}) and {other_item.rect_type} bounding box for `{other_item.field['description']}` ({other_item.rect})")
                if len(messages) >= 20:
                    messages.append("Aborting further checks; fix bounding boxes and try again")
                    return messages
        if current_item.rect_type == "entry":
            if "entry_text" in current_item.field:
                font_size = current_item.field["entry_text"].get("font_size", 14)
                entry_height = current_item.rect[3] - current_item.rect[1]
                if entry_height < font_size:
                    has_error = True
                    messages.append(f"FAILURE: entry bounding box height ({entry_height}) for `{current_item.field['description']}` is too short for the text content (font size: {font_size}). Increase the box height or decrease the font size.")
                    if len(messages) >= 20:
                        messages.append("Aborting further checks; fix bounding boxes and try again")
                        return messages

    if not has_error:
        messages.append("SUCCESS: All bounding boxes are valid")
    return messages

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: check_bounding_boxes.py [fields.json]")
        sys.exit(1)
    # Input file should be in the `fields.json` format described in forms.md.
    with open(sys.argv[1]) as f:
        messages = get_bounding_box_messages(f)
    for msg in messages:
        print(msg)
