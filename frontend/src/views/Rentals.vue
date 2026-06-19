<template>
  <div>
    <div class="toolbar">
      <el-button type="primary" @click="openRentalDialog()">新增租赁</el-button>
      <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 140px; margin-left: 12px;">
        <el-option label="进行中" value="active" />
        <el-option label="已归还" value="returned" />
      </el-select>
      <el-button type="warning" @click="showExpiringReminders" style="margin-left: 12px;">即将到期</el-button>
      <el-button type="danger" @click="showOverdueReminders" style="margin-left: 8px;">已逾期</el-button>
    </div>

    <el-table :data="filteredList" size="small" border>
      <el-table-column prop="id" label="编号" width="80" />
      <el-table-column label="乐器" width="160">
        <template #default="{ row }">
          {{ row.instrument?.name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="学员" width="120">
        <template #default="{ row }">
          {{ row.student?.name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="起租日期" width="110">
        <template #default="{ row }">{{ fmtDate(row.start_date) }}</template>
      </el-table-column>
      <el-table-column prop="end_date" label="到期日期" width="110">
        <template #default="{ row }">
          <span :class="{ 'text-danger': isOverdue(row) }">{{ fmtDate(row.end_date) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="rental_plan" label="租金方案" width="100">
        <template #default="{ row }">{{ rentalPlanText(row.rental_plan) }}</template>
      </el-table-column>
      <el-table-column prop="rent_amount" label="租金" width="100">
        <template #default="{ row }">¥{{ row.rent_amount }}</template>
      </el-table-column>
      <el-table-column prop="deposit_amount" label="押金" width="100">
        <template #default="{ row }">¥{{ row.deposit_amount }}</template>
      </el-table-column>
      <el-table-column prop="deposit_status" label="押金状态" width="100">
        <template #default="{ row }">
          <el-tag :type="depositStatusType(row.deposit_status)" size="small">{{ depositStatusText(row.deposit_status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" text @click="updateDeposit(row)" v-if="row.status === 'active'">押金</el-button>
          <el-button size="small" text type="success" @click="openReturnDialog(row)" v-if="row.status === 'active'">归还</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="rentalDialogVisible" :title="'新增租赁'" width="560px">
      <el-form :model="rentalForm" label-width="100px">
        <el-form-item label="乐器" required>
          <el-select v-model="rentalForm.instrument_id" style="width: 100%" placeholder="请选择乐器">
            <el-option v-for="i in availableInstruments" :key="i.id" :label="`${i.name} (${i.brand})`" :value="i.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学员" required>
          <el-select v-model="rentalForm.student_id" style="width: 100%" placeholder="请选择学员">
            <el-option v-for="s in students" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="起租日期" required>
          <el-date-picker v-model="rentalForm.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="到期日期" required>
          <el-date-picker v-model="rentalForm.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="租金方案" required>
          <el-select v-model="rentalForm.rental_plan" style="width: 100%">
            <el-option label="月租" value="monthly" />
            <el-option label="季租" value="quarterly" />
            <el-option label="半年租" value="half_year" />
            <el-option label="年租" value="yearly" />
          </el-select>
        </el-form-item>
        <el-form-item label="租金金额" required>
          <el-input-number v-model="rentalForm.rent_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="押金金额">
          <el-input-number v-model="rentalForm.deposit_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="押金状态">
          <el-select v-model="rentalForm.deposit_status" style="width: 100%">
            <el-option label="未支付" value="unpaid" />
            <el-option label="已支付" value="paid" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="rentalForm.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rentalDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRental">确认登记</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="returnDialogVisible" :title="'归还乐器'" width="520px">
      <el-form :model="returnForm" label-width="100px">
        <el-form-item label="乐器">
          <el-input :value="currentRental?.instrument?.name" disabled />
        </el-form-item>
        <el-form-item label="学员">
          <el-input :value="currentRental?.student?.name" disabled />
        </el-form-item>
        <el-form-item label="实际归还日期" required>
          <el-date-picker v-model="returnForm.actual_return_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="归还检查" required>
          <el-select v-model="returnForm.return_check" style="width: 100%">
            <el-option label="完好" value="good" />
            <el-option label="轻微磨损" value="minor_damage" />
            <el-option label="严重损坏" value="severe_damage" />
            <el-option label="遗失" value="lost" />
          </el-select>
          <div style="margin-top: 8px; font-size: 12px; color: #666;">
            <el-tag size="small" type="success">完好</el-tag> → 恢复可租
            <el-tag size="small" type="warning" style="margin-left: 8px;">轻微磨损/严重损坏</el-tag> → 标记维修（需确认后恢复）
            <el-tag size="small" type="danger" style="margin-left: 8px;">遗失</el-tag> → 标记报废
          </div>
        </el-form-item>
        <el-form-item label="损耗说明">
          <el-input v-model="returnForm.damage_description" type="textarea" :rows="3" placeholder="请描述乐器损耗情况..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="returnDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReturn">确认归还</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listRentals, createRental, returnRental, updateDepositStatus, getExpiringReminders, getOverdueReminders } from '../api/rental.js'
import { listInstruments } from '../api/instrument.js'
import { listStudents } from '../api/student.js'

const list = ref([])
const filterStatus = ref('')
const availableInstruments = ref([])
const students = ref([])

const rentalDialogVisible = ref(false)
const rentalForm = ref({
  instrument_id: '',
  student_id: '',
  start_date: '',
  end_date: '',
  rental_plan: 'monthly',
  rent_amount: 0,
  deposit_amount: 0,
  deposit_status: 'unpaid',
  remark: ''
})

const returnDialogVisible = ref(false)
const currentRental = ref(null)
const returnForm = ref({
  actual_return_date: '',
  return_check: '',
  damage_description: ''
})

const filteredList = computed(() => {
  if (!filterStatus.value) return list.value
  return list.value.filter(r => r.status === filterStatus.value)
})

function statusText(s) {
  const map = { active: '进行中', returned: '已归还' }
  return map[s] || s
}

function statusType(s) {
  const map = { active: 'primary', returned: 'success' }
  return map[s] || 'info'
}

function depositStatusText(s) {
  const map = { unpaid: '未支付', paid: '已支付', refunded: '已退还' }
  return map[s] || s
}

function depositStatusType(s) {
  const map = { unpaid: 'danger', paid: 'success', refunded: 'info' }
  return map[s] || 'info'
}

function rentalPlanText(p) {
  const map = { monthly: '月租', quarterly: '季租', half_year: '半年租', yearly: '年租' }
  return map[p] || p
}

function fmtDate(d) {
  if (!d) return '-'
  return d.split('T')[0]
}

function isOverdue(row) {
  if (row.status !== 'active') return false
  const end = new Date(row.end_date)
  const today = new Date()
  return end < today
}

async function load() {
  list.value = await listRentals()
  availableInstruments.value = (await listInstruments({ status: 'available' })) || []
  students.value = await listStudents()
}

function openRentalDialog() {
  rentalForm.value = {
    instrument_id: '',
    student_id: '',
    start_date: '',
    end_date: '',
    rental_plan: 'monthly',
    rent_amount: 0,
    deposit_amount: 0,
    deposit_status: 'unpaid',
    remark: ''
  }
  rentalDialogVisible.value = true
}

async function submitRental() {
  if (!rentalForm.value.instrument_id || !rentalForm.value.student_id) {
    ElMessage.warning('请选择乐器和学员')
    return
  }
  if (!rentalForm.value.start_date || !rentalForm.value.end_date) {
    ElMessage.warning('请选择日期')
    return
  }
  await createRental(rentalForm.value)
  rentalDialogVisible.value = false
  ElMessage.success('租赁登记成功')
  await load()
}

function openReturnDialog(row) {
  currentRental.value = row
  returnForm.value = {
    actual_return_date: new Date().toISOString().split('T')[0],
    return_check: '',
    damage_description: ''
  }
  returnDialogVisible.value = true
}

async function submitReturn() {
  if (!returnForm.value.return_check) {
    ElMessage.warning('请选择归还检查结果')
    return
  }
  await returnRental(currentRental.value.id, returnForm.value)
  returnDialogVisible.value = false
  ElMessage.success('归还登记成功')
  await load()
}

async function updateDeposit(row) {
  const { value } = await ElMessageBox.prompt('请选择押金状态', '更新押金状态', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputOptions: [
      { label: '未支付', value: 'unpaid' },
      { label: '已支付', value: 'paid' },
      { label: '已退还', value: 'refunded' }
    ],
    inputValue: row.deposit_status
  }).catch(() => ({}))
  if (!value) return
  await updateDepositStatus(row.id, value)
  await load()
}

async function showExpiringReminders() {
  const data = await getExpiringReminders(7)
  if (data.length === 0) {
    ElMessage.info('暂无即将到期的租赁')
    return
  }
  const msg = data.map(r => `${r.student?.name} 的 ${r.instrument?.name}（${fmtDate(r.end_date)}到期）`).join('\n')
  ElMessageBox.alert(msg, '即将到期提醒（7天内）', { type: 'warning' })
}

async function showOverdueReminders() {
  const data = await getOverdueReminders()
  if (data.length === 0) {
    ElMessage.info('暂无逾期的租赁')
    return
  }
  const msg = data.map(r => `${r.student?.name} 的 ${r.instrument?.name}（已于${fmtDate(r.end_date)}到期）`).join('\n')
  ElMessageBox.alert(msg, '已逾期提醒', { type: 'error' })
}

onMounted(load)
</script>

<style scoped>
.toolbar { margin-bottom: 12px; }
.text-danger { color: #f56c6c; font-weight: 500; }
</style>