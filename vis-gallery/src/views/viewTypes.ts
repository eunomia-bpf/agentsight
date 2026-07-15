import type { GalleryData, GalleryEvent, ViewState } from "../types";

export interface ViewProps {
  data: GalleryData;
  state: ViewState;
  events: GalleryEvent[];
  onChange: (patch: Partial<ViewState>) => void;
}
