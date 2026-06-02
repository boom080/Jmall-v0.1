# Jrunmall 命名迁移说明

## 1. 正式名称

项目正式名称统一为 **Jrunmall**。

命名约定：

- 展示名：`Jrunmall`
- Maven artifactId / 服务名：`jrunmall-*`
- Java / Docker / 本地环境变量新前缀：`JRUNMALL_*`
- 业务数据库：`jrunmall_pms`、`jrunmall_ums`、`jrunmall_oms`、`jrunmall_commerce`

## 2. 历史来源

GuliMall 是原始课程 / 旧底座名称。当前项目已经演进为 Jrunmall，本轮迁移将对外命名、数据库名、Maven artifactId、文档和脚本中的主要展示名迁到 Jrunmall。

## 3. 本轮已迁移

- 根 Maven 坐标改为 `com.shf.jrunmall:jrunmall`。
- 子模块 Maven artifactId 改为 `jrunmall-*`。
- Java 构建目标统一为 JDK 17。
- Lombok 升级到 `1.18.36`。
- `maven-compiler-plugin` 升级到 `3.13.0`。
- `maven-surefire-plugin` 升级到 `3.2.5`，并关闭测试 module path。
- `spring-boot-maven-plugin` 固定为 `2.7.18`，用于兼容 JDK 17 class file 的打包和本地启动。
- 业务数据库名改为 `jrunmall_pms`、`jrunmall_ums`、`jrunmall_oms`。
- Docker MySQL 首次初始化脚本改为创建 `jrunmall_*` 业务库。
- Java 配置优先读取 `JRUNMALL_*` 环境变量。
- `docs/Jrun.md`、`docs/run.md`、`docs/docker-sql.md`、`docs/order-progress.md`、`docs/seckill-redis-init.md` 已按新数据库名和新服务名更新。

## 4. 暂时保留的技术遗留

以下内容本轮暂不物理迁移：

- 物理目录仍保留 `gulimall-*`。原因：重命名目录会同时影响 IDE 模块、脚本路径、历史导入、Maven module 路径和大量本地配置。本轮先迁移 Maven artifactId，目录作为兼容路径保留。
- Java package 仍保留 `com.shf.gulimall`。原因：包名迁移会牵动所有 package 声明、import、Spring Boot 扫描路径、MapperScan、测试代码和资源路径，风险高于本轮 JDK 17 构建修复目标。
- 部分 Java 启动类、配置类和测试类文件名仍保留 `Gulimall*`。原因：这些 public class 名必须与当前文件名一致；本轮没有物理重命名 Java 文件，先作为技术遗留保留。
- Spring 配置前缀 `gulimall.*` 暂时保留。原因：已有 `@ConfigurationProperties` 和配置类依赖该技术前缀；对外环境变量已迁到 `JRUNMALL_*`。
- 旧环境变量 `GULIMALL_*` 保留为 fallback。新配置应使用 `JRUNMALL_*`，旧变量只用于短期兼容。
- 当前本地工作区目录仍是 `D:\java-projects\GuliMall`。文档命令使用真实路径，避免不可执行。
- `legacy/` 下的原课程材料不纳入本轮迁移。

## 5. 下一阶段建议

1. 统一重命名物理目录为 `jrunmall-*`，同步根 `pom.xml` 的 `<module>` 路径和脚本路径。
2. 全量迁移 Java package 到 `com.shf.jrunmall`，同步 import、MapperScan、测试和配置扫描路径。
3. 将 Spring 配置前缀从 `gulimall.*` 迁移为 `jrunmall.*`，同时保留一个版本的兼容映射。
4. 清理旧课程模块和 `legacy/` 之外残留的历史命名。
