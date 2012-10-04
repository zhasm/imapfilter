imapfilter
==========

###  说明
写这个程序的初衷在于练习使用 python 的某些语法特性，例如 class，继承，eval，\*args，**kwargs，generators.

主要用于个人邮件的整理。虽然 google 支持强大的filter 规则，毕竟不支持正则表达式。可以配合 gmail 的filter 来使用，也可以取代它。原理，gmail filter 过滤之后的邮件，漏网之鱼都在 Inbox 里；而本程序只 Focus 遗留在 Inbox 中的新邮件。

程序思路借鉴 spamassassin，自定义规则部分是借鉴 SA 的模式（而不是模仿其程序）。

### 实现的特性
可以根据邮件的任意 header、Body 来写规则（关键字或正则表达式），规则可以复用和叠加（meta），然后可以定义 action filter，将符合具体规则的邮件复制或转移至目的文件夹，或直接删除之。

### 规则名称
* 规则命名：`^[a-zA-Z_]+[a-zA-Z]\w+$` ，即，
    * 由3位及以上的字符组成，第一位可以是大小写字母或下划线，但不能是数字
    * 必须包含一位以上字母。

### 正则
* 程序、配置，均采用 python 风格的正则表达式。例如，可以使用 `(?i)` 设置正则为忽略大小写模式, 以及:
    *  i, Ignore Case
    *  L, Locale dependent (较不常用)
    *  m, multi-line (即^、$可匹配内部行首行尾)
    *  s, 点号通配任意字符（包括换行符）
    *  u, unicode dependent
    *  x, 注释空白模式，（忽略正则中的空白和注释）
        * comment: (?# … )
        * 所有空白字符（包括换行）视为不存在。正则中如果需要匹配空白字符，需要自行指定，例如 `\s`。
* 支持 look around. 注意 python regex 的 look behind 只支持 **定长字串** 。
* 支持命名和分组。为提升效率，使用分组时最好使用非捕获模式 `(?: …|… )`.


###规则分为两类：

#### 匹配规则
* 匹配规则，支持的规则类型：

规则类型   | 规则名称     | 子类型          |  正则部分  | 说明
-------- |------------ | -------------  | ------------ | -----------------------
header   | _rule_name_ | from, to, subject, cc, (any header)  | _REGEX_
meta     | _rule_name_ | meta and/or sub_rule  | N/A | meta 对表达式懒惰取值，返回True/False
eval     | _rule_name_ | 函数名(参数名), 例如: `has_image()` | N/A
to_all   | _rule_name_ || _REGEX_  | 常用规则； to, cc 的 alias rule。
involved | _rule_name_ || _REGEX_ | 常用规则； from, to, cc 的 alias rule。
content_type |  _rule_name_ || _REGEX_ |
body  |  _rule_name_ || _REGEX_ | 可匹配文本部分(text/plain)，如果有(text/html)，也可按html匹配。

* 说明
    * 规则定义在 `conf/*.cf` 文件里。
    * `header` 任意邮件头，正则匹配。所匹配的目标为utf-8编码的明文字串。

    * `eval` 任意函数，可以在 'msg.py' 里定义，内部通过 `eval(msg.EXPR)` 的方式进行求值。返回值应该是 boolean type 的。
    * `meta` 组合规则，可以包含其他 header rule and/or meta rule. 可以使用 and, or, not 以及对应的 &&, ||, ! 符号，来连接各子规则。使用 or 时，可以使用括号以便提升部分组合规则的运算优先级。
    * meta 规则的括号 是算术语法而不是正则语法，因此不适用 (?:…) 这种格式。
    * 规则类型、大小写不敏感；建议统一一种；
    * 规则名称，大小写敏感。不建议混用。
    * 程序的流程是，对于每封新邮件，逐一使用下面的 动作规则 进行匹配测试。一旦有匹配，立即执行动作，不再进行其他规则的测试。可以善用 meta 规则，只匹配需要的。
    * body 规则比较低效。因为对于每一封新邮件，都要顺次执行所有的动作规则。因此如果动作规则中包含body rule，对性能影响较大。


#### 动作规则

规则类型 | 规则名称 | 目的地
--------|--------|-------
move    | _rule_name_ | _dest_folder_name_
copy    | _rule_name_ | _dest_folder_name_
delete    | _rule_name_ | N/A

##### 说明

* 规则定义在 `conf/filter.conf` 文件里。
* 此处的 _rule_name_ 即上面定义过的rule_name，可以是任意类型的规则，例如header, body, meta, eval, …。
* 如果规则名称不存在对应的定义，则报错（TODO: 事先检测）。
* 对于 move, copy动作，程序会在启动时遍历所有的目的地文件夹。如果不存在，则主动创建之。文件支持嵌套。
* 如果任何过滤器都无法匹配某新邮件，则该邮件会被移动到默认文件夹。（定义在settings.py 里的default_not_matched_dest 选项，默认值为 `NoWhere`）。


### TODO

* 规则库平滑更新。
* 使用 UI 界面，提供更友好的写规则界面。
