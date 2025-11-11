import { create } from "zustand";

export const useCreateStore = create((set) => ({
  toc: [],
  activeHeadingId: null,
  setToc: (items) => set({ toc: items }),
  setActiveHeading: (id) => set({ activeHeadingId: id }),
}));

