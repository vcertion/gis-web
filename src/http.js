// import axios from 'axios';


// axios.defaults.timeout = 60000;
// axios.defaults.baseURL = 'http://127.0.0.1:5000';

// export default axios;

import axios from 'axios';

export const API_BASE = 'https://SQ246-gis-web.hf.space';

const http = axios.create({
  baseURL: 'https://SQ246-gis-web.hf.space',
  timeout: 15000,
});

// export default http;

// import axios from 'axios';

// // 根据环境设置不同的baseURL
// const isDevelopment = process.env.NODE_ENV === 'development';
// const baseURL = isDevelopment ? 'http://127.0.0.1:5000' : 'https://SQ246-gis-web.hf.space';

// const http = axios.create({
//   baseURL: baseURL,
//   timeout: 60000, // 使用20秒超时
// });

// export default http;
// export const API_BASE = baseURL;

