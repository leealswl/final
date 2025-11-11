import axios from "axios";

const api = axios.create({
  baseURL: "/backend",
  withCredentials: true,
  timeout: 50000,
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;