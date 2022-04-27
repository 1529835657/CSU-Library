# CSU Library
中南大学图书馆预约、签到、签离助手。

### 配置步骤
1. 将项目Fork到自己仓库。

2. 配置私密参数：依次点击上栏 [Setting] -> [Security] -> [Secrets] -> [Actions] -> [New repository secrets] 添加学号和门户网密码，示例如下：
    | Name |    Value   |
    |:----:|:----------:|
    |`USER`|`820******2`|
    |`PWD` |`**********`|

3. 修改配置文件config.ini：修改 SEAT 数组中的项为你想预约的座位集(**!!!请一定修改所有项以防止冲突**，如无特殊情况请避开三楼A区)。

### 使用方法
配置完毕后，程序会在每天6:20左右预约下一天的座位，7:40左右执行签到，21:20左右执行签离。
所以请您入馆前先手动临时离开再刷卡进馆，出馆、临时离开请不要刷卡，也不要在签到机上做任何操作。

### 附:手动操作方法
若要手动预约、签到、临时离开、签离，请在微信客户端打开如下链接：
| 操作 |                               链接                                   |
|:---:|:--------------------------------------------------------------------:|
| 签到 |http://www.skalibrary.net/wx/scancheck?school=csu&type=1&t=99999999999|
| 暂离 |http://www.skalibrary.net/wx/scancheck?school=csu&type=2&t=99999999999|
| 签离 |http://www.skalibrary.net/wx/scancheck?school=csu&type=3&t=99999999999|
