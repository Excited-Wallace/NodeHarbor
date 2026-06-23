/**
 * 客户端下载 API 封装
 * 
 * 接口：
 *   - getClients(): GET /api/clients 获取支持的客户端列表及版本信息
 *   - fetchClient(name, platform): POST /api/clients/{name}/fetch 触发服务器下载
 *   - downloadClient(name, platform): GET /api/clients/{name}/download 下载缓存文件
 *   - getStatus(name): GET /api/clients/{name}/status 查询下载进度
 */
