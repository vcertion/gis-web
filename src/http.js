// import axios from 'axios';


// axios.defaults.timeout = 5000;
// axios.defaults.baseURL = 'http://127.0.0.1:5000';

// export default axios;

import axios from 'axios'

const http = axios.create({
  baseURL: 'https://SQ246-gis-web.hf.space',
  timeout: 15000
})

export default http

