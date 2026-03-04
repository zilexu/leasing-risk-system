from django.db import models

class Customer(models.Model):
    """承租人（客户）实体"""
    name = models.CharField(max_length=100, verbose_name="客户名称")
    credit_code = models.CharField(max_length=18, unique=True, verbose_name="统一社会信用代码/身份证号")
    contact_phone = models.CharField(max_length=20, verbose_name="联系电话")
    
    # 逻辑删除标志
    is_active = models.BooleanField(default=True, verbose_name="是否有效")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def __str__(self):
        return self.name

class LeaseContract(models.Model):
    """租赁合同"""
    STATUS_CHOICES = [
        ('ACTIVE', '生效中'),
        ('SETTLED', '已结清'),
        ('DEFAULT', '违约'),
    ]
    
    contract_no = models.CharField(max_length=50, unique=True, verbose_name="合同编号")
    # 合同必须关联客户，且客户不能被物理删除
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='contracts', verbose_name="关联客户")
    
    # 金融核心字段必须用 DecimalField 保证精度，不能用 FloatField
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="合同总金额")
    start_date = models.DateField(verbose_name="起租日期")
    end_date = models.DateField(verbose_name="到期日期")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', verbose_name="合同状态")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def __str__(self):
        return self.contract_no

class LeasedAsset(models.Model):
    """租赁物核心台账"""
    STATUS_CHOICES = [
        ('IN_USE', '使用中'),
        ('MAINTENANCE', '维修中'),
        ('DISPOSED', '已处置'),
    ]
    
    asset_name = models.CharField(max_length=100, verbose_name="租赁物名称")
    asset_sn = models.CharField(max_length=100, unique=True, verbose_name="设备识别码/车架号")
    
    # 资产必须关联具体合同
    contract = models.ForeignKey(LeaseContract, on_delete=models.PROTECT, related_name='assets', verbose_name="所属合同")
    
    # 估值追踪机制
    initial_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="初始采购/评估价值")
    current_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="当前重估价值")
    
    physical_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_USE', verbose_name="物理状态")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="入账时间")

    def __str__(self):
        return f"{self.asset_name} ({self.asset_sn})"

class InspectionLog(models.Model):
    """巡检与检查历史大表"""
    RISK_LEVEL_CHOICES = [
        ('GREEN', '绿灯 - 正常'),
        ('YELLOW', '黄灯 - 需关注'),
        ('RED', '红灯 - 风险警报'),
    ]
    
    # 强制保护，不允许资产被物理删除导致流水成无头账
    asset = models.ForeignKey(LeasedAsset, on_delete=models.PROTECT, related_name='inspection_logs', verbose_name="关联租赁物")
    
    inspection_date = models.DateField(verbose_name="巡检日期")
    inspector = models.CharField(max_length=50, verbose_name="巡检人员")
    
    # 每次巡检记录当时的估值
    revalued_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="本次巡检估值")
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='GREEN', verbose_name="风险预警灯号")
    
    remarks = models.TextField(blank=True, null=True, verbose_name="巡检备注/风险描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="记录创建时间")

    def __str__(self):
        return f"{self.asset.asset_name} - {self.inspection_date} ({self.get_risk_level_display()})"
