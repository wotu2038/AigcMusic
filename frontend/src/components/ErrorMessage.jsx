import './ErrorMessage.css';

/**
 * 错误提示组件
 */
function ErrorMessage({ message, onClose }) {
    if (!message) return null;
    
    return (
        <div className="error-message">
            <span className="error-icon">⚠️</span>
            <span className="error-text">{message}</span>
            {onClose && (
                <button className="error-close" onClick={onClose}>×</button>
            )}
        </div>
    );
}

export default ErrorMessage;

