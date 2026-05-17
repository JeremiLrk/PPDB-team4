// Frontend bootstrap entrypoint.

import { StrictMode } from 'react'
import { BrowserRouter } from 'react-router-dom';
import ReactDOM from 'react-dom/client';
import App from '@/app/App.jsx'
import '@/style/index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
    <StrictMode>
        <BrowserRouter>
            <App />
        </BrowserRouter>
    </StrictMode>,
)
