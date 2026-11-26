import ReactDOM from 'react-dom/client';
import App from './App';
import { StateProvider } from './state/store';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <StateProvider>
    <App />
  </StateProvider>,
);
