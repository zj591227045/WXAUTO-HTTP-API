/**
 * 统一API测试工具类
 */
class UnifiedApiTester {
    constructor(containerId, config = {}) {
        console.log(`正在创建API测试工具: ${containerId}`, config);

        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`容器元素未找到: ${containerId}`);
            return;
        }

        this.config = {
            baseUrl: config.baseUrl || window.location.origin,
            apiKey: config.apiKey || 'test-key-2',
            endpoint: config.endpoint || '',
            method: config.method || 'POST',
            parameters: config.parameters || [],
            ...config
        };

        console.log(`API测试工具配置:`, this.config);

        this.loadConfigFromServer().then(() => {
            this.init();
        }).catch(() => {
            // 如果配置加载失败，直接使用默认配置初始化
            this.init();
        });
    }

    async loadConfigFromServer() {
        try {
            const response = await fetch('/api/config/get-api-settings');
            if (response.ok) {
                const data = await response.json();
                if (data.code === 0) {
                    this.config.baseUrl = data.data.base_url || this.config.baseUrl;
                    this.config.apiKey = data.data.api_key || this.config.apiKey;
                }
            }
        } catch (error) {
            // 静默处理配置加载失败，使用默认值
            console.debug('使用默认配置:', error.message);
        }
    }

    init() {
        this.render();
        this.bindEvents();
        this.updateCurlPreview();
    }

    render() {
        const html = `
            <!-- CURL预览区域 - 置于顶部 -->
            <div class="api-curl-preview">
                <div class="curl-preview-header">
                    <i class="bi bi-terminal"></i>
                    CURL命令预览
                </div>
                <div class="curl-preview"></div>
            </div>

            <!-- 表单区域 -->
            <div class="api-form-section">
                <h6><i class="bi bi-gear"></i> 请求参数</h6>
                <form class="api-test-form">
                    ${this.renderFormFields()}
                    <div class="button-group">
                        <button type="submit" class="btn-primary">
                            <i class="bi bi-play-fill"></i>
                            发送请求
                        </button>
                        <button type="button" class="btn-secondary copy-curl-btn">
                            <i class="bi bi-clipboard"></i>
                            复制CURL
                        </button>
                    </div>
                </form>
            </div>

            <!-- 响应结果区域 -->
            <div class="response-section">
                <div class="response-header">
                    <i class="bi bi-arrow-down-circle"></i>
                    响应结果
                </div>
                <pre class="response-content"></pre>
            </div>
        `;

        this.container.innerHTML = html;
        this.container.className = 'unified-api-tester';
    }

    renderFormFields() {
        let fieldsHtml = '';
        
        // 基础配置字段
        fieldsHtml += `
            <div class="form-group">
                <label class="optional">服务器地址</label>
                <input type="text" class="form-control" name="base_url" value="${this.config.baseUrl}">
                <div class="form-text">API服务器的基础地址</div>
            </div>
            <div class="form-group">
                <label class="optional">API密钥</label>
                <input type="text" class="form-control" name="api_key" value="${this.config.apiKey}">
                <div class="form-text">用于身份验证的API密钥</div>
            </div>
        `;
        
        // 动态参数字段
        this.config.parameters.forEach(param => {
            const required = param.required ? 'required' : 'optional';
            const requiredAttr = param.required ? 'required' : '';
            
            fieldsHtml += `
                <div class="form-group">
                    <label class="${required}">${param.label}</label>
                    ${this.renderFormField(param, requiredAttr)}
                    <div class="form-text">${param.description || ''}</div>
                </div>
            `;
        });
        
        return fieldsHtml;
    }

    renderFormField(param, requiredAttr) {
        switch (param.type) {
            case 'textarea':
                return `<textarea class="form-control" name="${param.name}" placeholder="${param.placeholder || ''}" ${requiredAttr}>${param.default || ''}</textarea>`;
            case 'select':
                const options = param.options.map(opt => 
                    `<option value="${opt.value}" ${opt.selected ? 'selected' : ''}>${opt.label}</option>`
                ).join('');
                return `<select class="form-control" name="${param.name}" ${requiredAttr}>${options}</select>`;
            case 'number':
                return `<input type="number" class="form-control" name="${param.name}" placeholder="${param.placeholder || ''}" value="${param.default || ''}" ${requiredAttr}>`;
            case 'checkbox':
                return `<input type="checkbox" class="form-check-input" name="${param.name}" ${param.default ? 'checked' : ''} ${requiredAttr}>`;
            default:
                return `<input type="text" class="form-control" name="${param.name}" placeholder="${param.placeholder || ''}" value="${param.default || ''}" ${requiredAttr}>`;
        }
    }

    bindEvents() {
        const form = this.container.querySelector('.api-test-form');
        const copyBtn = this.container.querySelector('.copy-curl-btn');

        if (!form) {
            console.error('API测试表单未找到');
            return;
        }

        if (!copyBtn) {
            console.error('复制CURL按钮未找到');
            return;
        }

        // 表单提交事件
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendRequest();
        });

        // 复制CURL命令事件
        copyBtn.addEventListener('click', () => {
            this.copyCurlCommand();
        });

        // 表单字段变化时更新CURL预览
        form.addEventListener('input', () => {
            this.updateCurlPreview();
        });

        // 实时验证
        const formControls = form.querySelectorAll('.form-control');
        if (formControls) {
            formControls.forEach(input => {
                if (input) {
                    input.addEventListener('input', () => {
                        this.validateField(input);
                    });
                }
            });
        }
    }

    validateField(input) {
        if (!input || !input.classList) {
            console.error('无效的输入元素');
            return;
        }

        if (input.hasAttribute('required')) {
            if (input.value.trim()) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
            }
        }
    }

    getFormData() {
        const form = this.container.querySelector('.api-test-form');
        if (!form) {
            console.error('API测试表单未找到');
            return {};
        }

        const formData = new FormData(form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            if (key === 'at_list' && value) {
                data[key] = value.split(',').map(s => s.trim()).filter(s => s);
            } else if (key === 'file_paths' && value) {
                data[key] = value.split(',').map(s => s.trim()).filter(s => s);
            } else if (key === 'members' && value) {
                // 处理members字段，支持逗号分隔的字符串转换为数组
                data[key] = value.split(',').map(s => s.trim()).filter(s => s);
            } else if (value) {
                data[key] = value;
            }
        }

        return data;
    }

    generateCurlCommand() {
        const data = this.getFormData();
        const baseUrl = data.base_url || this.config.baseUrl;
        const apiKey = data.api_key || this.config.apiKey;
        
        // 移除配置字段
        delete data.base_url;
        delete data.api_key;
        
        const url = `${baseUrl}${this.config.endpoint}`;
        let curl = `curl -X ${this.config.method} "${url}"`;
        
        // 添加headers
        curl += ` \\\n  -H "X-API-Key: ${apiKey}"`;
        curl += ` \\\n  -H "Content-Type: application/json"`;
        
        // 添加数据
        if (this.config.method !== 'GET' && Object.keys(data).length > 0) {
            curl += ` \\\n  -d '${JSON.stringify(data, null, 2)}'`;
        } else if (this.config.method === 'GET' && Object.keys(data).length > 0) {
            const params = new URLSearchParams(data);
            curl = `curl -X GET "${url}?${params}"`;
            curl += ` \\\n  -H "X-API-Key: ${apiKey}"`;
        }
        
        return curl;
    }

    updateCurlPreview() {
        const curlPreview = this.container.querySelector('.curl-preview');
        if (!curlPreview) {
            console.error('CURL预览元素未找到');
            return;
        }
        curlPreview.textContent = this.generateCurlCommand();
    }

    async copyCurlCommand() {
        const curlCommand = this.generateCurlCommand();
        try {
            await navigator.clipboard.writeText(curlCommand);
            this.showToast('CURL命令已复制到剪贴板', 'success');
        } catch (err) {
            console.error('复制失败:', err);
            this.showToast('复制失败，请手动复制', 'error');
        }
    }

    async sendRequest() {
        const data = this.getFormData();
        const baseUrl = data.base_url || this.config.baseUrl;
        const apiKey = data.api_key || this.config.apiKey;
        
        // 移除配置字段
        delete data.base_url;
        delete data.api_key;
        
        const responseSection = this.container.querySelector('.response-section');
        const responseContent = this.container.querySelector('.response-content');
        const submitBtn = this.container.querySelector('.btn-primary');
        
        if (!responseSection || !responseContent || !submitBtn) {
            console.error('响应区域元素未找到');
            return;
        }

        try {
            // 设置加载状态
            this.container.classList.add('loading');
            submitBtn.disabled = true;
            responseSection.classList.remove('success', 'error');
            
            const url = this.config.method === 'GET' ?
                `${baseUrl}${this.config.endpoint}?${new URLSearchParams(data)}` :
                `${baseUrl}${this.config.endpoint}`;
            
            const options = {
                method: this.config.method,
                headers: {
                    'X-API-Key': apiKey,
                    'Content-Type': 'application/json'
                }
            };
            
            if (this.config.method !== 'GET') {
                options.body = JSON.stringify(data);
            }
            
            responseContent.textContent = '🚀 发送请求中...';
            responseSection.style.display = 'block';
            
            const response = await fetch(url, options);
            const result = await response.json();
            
            // 格式化响应内容
            responseContent.textContent = JSON.stringify(result, null, 2);
            
            // 设置成功/错误状态
            if (response.ok && result.code === 0) {
                responseSection.classList.add('success');
                this.showToast('请求成功', 'success');
            } else {
                responseSection.classList.add('error');
                this.showToast('请求失败', 'error');
            }
            
        } catch (error) {
            responseContent.textContent = `❌ 请求失败: ${error.message}`;
            responseSection.classList.add('error');
            responseSection.style.display = 'block';
            this.showToast(`请求失败: ${error.message}`, 'error');
        } finally {
            // 移除加载状态
            this.container.classList.remove('loading');
            if (submitBtn) {
                submitBtn.disabled = false;
            }
        }
    }

    showToast(message, type = 'info') {
        // 简单的toast提示实现
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 9999;
            animation: slideInRight 0.3s ease-out;
        `;
        
        switch (type) {
            case 'success':
                toast.style.background = '#10b981';
                break;
            case 'error':
                toast.style.background = '#ef4444';
                break;
            default:
                toast.style.background = '#6b7280';
        }
        
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// 工厂函数，用于快速创建API测试器
function createApiTester(containerId, config) {
    return new UnifiedApiTester(containerId, config);
}
