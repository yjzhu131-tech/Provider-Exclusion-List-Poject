EXCLTYPE: 这是 exclusion type / exclusion authority code，表示这个人或机构是根据哪条法律/规则被排除的。
EXCLDATE: 这是 exclusion effective date，也就是 exclusion 生效日期。
REINDATE: 这是 reinstatement date，也就是恢复资格日期。都是0
SANCDATE: 这是 sanction date，在 Georgia OIG list 里基本可以当成 Georgia exclusion/sanction 的生效日期。


source
  = 谁发布的名单

import
  = 我哪天导入了哪个文件

party
  = 名单上的人或机构是谁

identifier
  = 这个人或机构有什么编号，比如 NPI,
  因为一个人/机构理论上可能有多个 identifier 所以要和party分开

exclusion
  = 这个人或机构为什么、什么时候被排除

dbdiagram: 
many-to-one ‘ref: > table.column’
one-to-one 'ref: - table.column'
many-to-many 'ref: <> table.column'
