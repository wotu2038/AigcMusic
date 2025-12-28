import { BrowserRouter } from 'react-router-dom';
import AppRouter from './router';
import Header from './components/Header';
import './App.css';

function App() {
    return (
        <BrowserRouter>
            <div className="app">
                <Header />
                <main className="app-main">
                    <AppRouter />
                </main>
            </div>
        </BrowserRouter>
    );
}

export default App;
