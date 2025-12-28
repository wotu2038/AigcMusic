import './Loading.css';

/**
 * 加载动画组件
 */
function Loading({ text = '加载中...' }) {
    return (
        <div className="loading-container">
            <div className="loading-spinner"></div>
            <p className="loading-text">{text}</p>
        </div>
    );
}

export default Loading;

