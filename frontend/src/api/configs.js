/**
 * 配置文件 API 封装
 * 
 * 接口：
 *   - getConfigs(): GET /api/configs 获取配置列表
 *   - uploadConfig(formData): POST /api/configs/upload 上传配置文件
 *   - getConfigDetail(id): GET /api/configs/{id} 获取配置详情
 *   - downloadConfig(id): GET /api/configs/{id}/download 下载配置文件
 *   - getContent(id): GET /api/configs/{id}/content 获取文件文本（编辑用）
 *   - updateContent(id, content): PUT /api/configs/{id}/content 更新文件内容
 *   - deleteConfig(id): DELETE /api/configs/{id} 删除配置文件
 */
