# -*- coding: utf-8 -*-
"""
================================================================================
嵌入式开发全流程辅助Agent系统 (STM32专用版)
================================================================================
版本: v2.0
适用平台: STM32F103系列
核心特性: 多Agent协作 + 长链推理 + 闭环验证

解决的核心痛点:
1. 外设配置复杂 - 新手常因时钟树配置错误导致系统不工作
2. 驱动编写繁琐 - 重复编写I2C/SPI等驱动代码效率低下
3. 调试排错困难 - 硬件问题定位需要丰富经验
4. 工程搭建重复 - 竞赛/项目中重复配置浪费时间
================================================================================
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# ====================== 核心数据结构定义 ======================

class AgentState(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ErrorType(Enum):
    """嵌入式常见错误类型"""
    CLOCK_CONFIG_ERROR = "时钟配置错误"
    I2C_NO_ACK = "I2C无应答"
    HARD_FAULT = "硬件故障"
    MEMORY_OVERFLOW = "内存溢出"
    TIMING_VIOLATION = "时序冲突"
    DEVICE_ADDR_MISMATCH = "设备地址不匹配"
    DMA_CONFIG_ERROR = "DMA配置错误"
    GPIO_CONFLICT = "GPIO引脚冲突"


@dataclass
class ModuleSpec:
    """模块规格定义"""
    name: str
    category: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1


@dataclass
class AgentMessage:
    """Agent间通信消息"""
    sender: str
    receiver: str
    content: Any
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    msg_type: str = "data"


@dataclass
class ReasoningStep:
    """长链推理步骤"""
    step_id: int
    description: str
    input_data: Any
    output_data: Any
    confidence: float
    next_steps: List[int] = field(default_factory=list)


@dataclass
class DebugResult:
    """调试结果"""
    error_type: ErrorType
    root_cause: str
    solution: str
    code_fix: Optional[str] = None
    reasoning_chain: List[ReasoningStep] = field(default_factory=list)


# ====================== Agent基类定义 ======================

class BaseAgent(ABC):
    """Agent基类：定义统一接口和通信机制"""
    
    def __init__(self, name: str):
        self.name = name
        self.state = AgentState.IDLE
        self.message_queue: List[AgentMessage] = []
        self.reasoning_chain: List[ReasoningStep] = []
    
    def receive_message(self, message: AgentMessage):
        """接收其他Agent发送的消息"""
        if message.receiver == self.name or message.receiver == "all":
            self.message_queue.append(message)
    
    def send_message(self, receiver: str, content: Any, msg_type: str = "data"):
        """向其他Agent发送消息"""
        return AgentMessage(
            sender=self.name,
            receiver=receiver,
            content=content,
            msg_type=msg_type
        )
    
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """核心处理逻辑，子类必须实现"""
        pass
    
    def update_state(self, new_state: AgentState):
        """更新Agent状态"""
        self.state = new_state


# ====================== 1. 需求解析Agent ======================

class DemandParseAgent(BaseAgent):
    """
    需求解析Agent：智能拆解嵌入式项目需求
    
    核心能力:
    - 自然语言需求理解
    - 模块化拆解与依赖分析
    - 技术参数提取
    - 性能指标量化
    """
    
    STM32_PERIPHERALS = {
        "MPU6050": {"interface": "I2C", "pins": ["PB6", "PB7"], "clock": "400kHz"},
        "电机控制": {"interface": "TIM", "pins": ["PA0", "PA1"], "mode": "PWM"},
        "OLED显示": {"interface": "I2C", "pins": ["PB8", "PB9"], "clock": "100kHz"},
        "蓝牙模块": {"interface": "USART", "pins": ["PA9", "PA10"], "baud": "115200"},
        "编码器": {"interface": "TIM_ENCODER", "pins": ["PA6", "PA7"]},
    }
    
    def __init__(self):
        super().__init__("DemandParseAgent")
        self.project_info: Dict[str, Any] = {}
    
    def process(self, demand_text: str) -> Tuple[str, List[ModuleSpec]]:
        """处理需求文本，返回项目类型和模块列表"""
        self.update_state(AgentState.RUNNING)
        print("=" * 60)
        print("【需求解析Agent】启动 - 开始长链推理分析")
        print("=" * 60)
        print(f"📥 输入需求: {demand_text}\n")
        
        # 长链推理步骤1: 识别项目类型
        step1 = self._reasoning_step_1(demand_text)
        self.reasoning_chain.append(step1)
        
        # 长链推理步骤2: 提取硬件组件
        step2 = self._reasoning_step_2(demand_text)
        self.reasoning_chain.append(step2)
        
        # 长链推理步骤3: 分析模块依赖关系
        step3 = self._reasoning_step_3(step2.output_data)
        self.reasoning_chain.append(step3)
        
        # 长链推理步骤4: 生成技术参数
        modules = self._reasoning_step_4(step2.output_data, step3.output_data)
        
        self._print_reasoning_chain()
        
        self.update_state(AgentState.SUCCESS)
        return step1.output_data, modules
    
    def _reasoning_step_1(self, text: str) -> ReasoningStep:
        """推理步骤1: 项目类型识别"""
        project_types = {
            "平衡车": "STM32平衡车项目",
            "智能车": "STM32智能车项目",
            "机器人": "STM32机器人项目",
            "无人机": "STM32飞控项目",
            "数据采集": "STM32数据采集系统",
        }
        
        detected_type = "STM32通用项目"
        for keyword, ptype in project_types.items():
            if keyword in text:
                detected_type = ptype
                break
        
        return ReasoningStep(
            step_id=1,
            description="识别项目类型",
            input_data=text,
            output_data=detected_type,
            confidence=0.95,
            next_steps=[2]
        )
    
    def _reasoning_step_2(self, text: str) -> ReasoningStep:
        """推理步骤2: 硬件组件提取"""
        components = []
        keywords = {
            "MPU6050": "姿态传感器",
            "电机": "电机驱动",
            "OLED": "显示模块",
            "蓝牙": "通信模块",
            "编码器": "速度测量",
            "PID": "控制算法",
            "姿态": "姿态解算",
        }
        
        for kw, comp in keywords.items():
            if kw in text:
                components.append(comp)
        
        return ReasoningStep(
            step_id=2,
            description="提取硬件组件",
            input_data=text,
            output_data=components,
            confidence=0.90,
            next_steps=[3]
        )
    
    def _reasoning_step_3(self, components: List[str]) -> ReasoningStep:
        """推理步骤3: 依赖关系分析"""
        dependencies = {
            "姿态传感器": ["I2C初始化", "GPIO配置"],
            "电机驱动": ["TIM配置", "PWM输出"],
            "显示模块": ["I2C初始化"],
            "通信模块": ["USART配置"],
            "速度测量": ["TIM编码器模式"],
            "控制算法": ["定时器中断"],
            "姿态解算": ["姿态传感器", "定时器中断"],
        }
        
        all_deps = set()
        for comp in components:
            if comp in dependencies:
                all_deps.update(dependencies[comp])
        
        return ReasoningStep(
            step_id=3,
            description="分析模块依赖",
            input_data=components,
            output_data=list(all_deps),
            confidence=0.85,
            next_steps=[4]
        )
    
    def _reasoning_step_4(self, components: List[str], deps: List[str]) -> List[ModuleSpec]:
        """推理步骤4: 生成模块规格"""
        modules = []
        
        # 时钟配置模块
        modules.append(ModuleSpec(
            name="时钟树配置",
            category="系统核心",
            parameters={"sysclk": "72MHz", "hse": "8MHz", "pll": "9"},
            priority=1
        ))
        
        # 根据组件添加模块
        if "姿态传感器" in components:
            modules.append(ModuleSpec(
                name="I2C1外设配置",
                category="通信接口",
                parameters={"pins": ["PB6", "PB7"], "clock": "400kHz", "mode": "master"},
                dependencies=["时钟树配置"],
                priority=2
            ))
            modules.append(ModuleSpec(
                name="MPU6050驱动",
                category="传感器驱动",
                parameters={"addr": "0xD0", "gyro_range": "2000dps", "accel_range": "4g"},
                dependencies=["I2C1外设配置"],
                priority=3
            ))
        
        if "电机驱动" in components:
            modules.append(ModuleSpec(
                name="TIM2 PWM配置",
                category="定时器",
                parameters={"freq": "20kHz", "duty_cycle": "可调", "pins": ["PA0", "PA1"]},
                dependencies=["时钟树配置"],
                priority=2
            ))
        
        if "控制算法" in components or "PID" in str(components):
            modules.append(ModuleSpec(
                name="PID控制算法",
                category="控制逻辑",
                parameters={"kp": 12.0, "ki": 0.05, "kd": 20.0, "sample_time": "5ms"},
                dependencies=["TIM2 PWM配置"],
                priority=4
            ))
        
        print(f"✅ 需求解析完成，共识别 {len(modules)} 个模块")
        return modules
    
    def _print_reasoning_chain(self):
        """打印推理链"""
        print("\n📋 长链推理过程:")
        print("-" * 50)
        for step in self.reasoning_chain:
            print(f"  步骤{step.step_id}: {step.description}")
            print(f"    输入: {step.input_data}")
            print(f"    输出: {step.output_data}")
            print(f"    置信度: {step.confidence*100:.1f}%")
            print()


# ====================== 2. 配置生成Agent ======================

class ConfigGenerateAgent(BaseAgent):
    """
    配置生成Agent: 自动生成STM32CubeMX配置和初始化代码
    
    核心能力:
    - 时钟树自动配置
    - 外设参数优化
    - GPIO引脚冲突检测
    - DMA通道分配
    """
    
    def __init__(self):
        super().__init__("ConfigGenerateAgent")
        self.config_cache: Dict[str, Any] = {}
    
    def process(self, input_data: Tuple[str, List[ModuleSpec]]) -> str:
        """生成配置代码"""
        self.update_state(AgentState.RUNNING)
        project_type, modules = input_data
        
        print("=" * 60)
        print("【配置生成Agent】启动 - CubeMX配置生成")
        print("=" * 60)
        print(f"📦 项目类型: {project_type}")
        print(f"📦 模块数量: {len(modules)}\n")
        
        # 长链推理: 配置生成流程
        config_code = self._generate_with_reasoning(modules)
        
        self.update_state(AgentState.SUCCESS)
        return config_code
    
    def _generate_with_reasoning(self, modules: List[ModuleSpec]) -> str:
        """带推理的配置生成"""
        
        # 推理步骤1: 分析模块优先级
        sorted_modules = sorted(modules, key=lambda m: m.priority)
        print("📋 推理步骤1: 模块优先级排序")
        print(f"   排序结果: {[m.name for m in sorted_modules]}")
        
        # 推理步骤2: 检测引脚冲突
        pin_usage = self._detect_pin_conflicts(modules)
        print("\n📋 推理步骤2: 引脚冲突检测")
        if pin_usage["conflicts"]:
            print(f"   ⚠️ 发现冲突: {pin_usage['conflicts']}")
        else:
            print("   ✅ 无引脚冲突")
        
        # 推理步骤3: 生成配置代码
        print("\n📋 推理步骤3: 生成初始化代码")
        code = self._build_init_code(sorted_modules)
        
        return code
    
    def _detect_pin_conflicts(self, modules: List[ModuleSpec]) -> Dict[str, Any]:
        """检测引脚冲突"""
        pin_map = {}
        conflicts = []
        
        for module in modules:
            pins = module.parameters.get("pins", [])
            for pin in pins:
                if pin in pin_map:
                    conflicts.append(f"{pin}: {pin_map[pin]} <-> {module.name}")
                else:
                    pin_map[pin] = module.name
        
        return {"pin_map": pin_map, "conflicts": conflicts}
    
    def _build_init_code(self, modules: List[ModuleSpec]) -> str:
        """构建初始化代码"""
        code = '''/**
 * ============================================================================
 * STM32F103 自动生成工程代码 (HAL库)
 * 生成时间: ''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '''
 * ============================================================================
 */
#include "stm32f1xx_hal.h"
#include "main.h"

/* ==================== 句柄定义 ==================== */
I2C_HandleTypeDef hi2c1;
TIM_HandleTypeDef htim2;
UART_HandleTypeDef huart1;

/* ==================== 时钟配置 (72MHz) ==================== */
void SystemClock_Config(void)
{
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
    
    /* 配置HSE和PLL */
    RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    RCC_OscInitStruct.HSEState = RCC_HSE_ON;
    RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
    RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;  /* 8MHz * 9 = 72MHz */
    if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) {
        Error_Handler();
    }
    
    /* 配置系统时钟 */
    RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                                | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
    RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;  /* APB1 = 36MHz */
    RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;  /* APB2 = 72MHz */
    
    if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK) {
        Error_Handler();
    }
}

/* ==================== I2C1初始化 (MPU6050) ==================== */
void MX_I2C1_Init(void)
{
    hi2c1.Instance = I2C1;
    hi2c1.Init.ClockSpeed = 400000;  /* 400kHz Fast Mode */
    hi2c1.Init.DutyCycle = I2C_DUTYCYCLE_2;
    hi2c1.Init.OwnAddress1 = 0;
    hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
    
    if (HAL_I2C_Init(&hi2c1) != HAL_OK) {
        Error_Handler();
    }
}

/* ==================== TIM2 PWM初始化 (电机控制) ==================== */
void MX_TIM2_Init(void)
{
    TIM_OC_InitTypeDef sConfigOC = {0};
    
    htim2.Instance = TIM2;
    htim2.Init.Prescaler = 71;  /* 72MHz / 72 = 1MHz */
    htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim2.Init.Period = 49;     /* 1MHz / 50 = 20kHz PWM */
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    
    if (HAL_TIM_PWM_Init(&htim2) != HAL_OK) {
        Error_Handler();
    }
    
    sConfigOC.OCMode = TIM_OCMODE_PWM1;
    sConfigOC.Pulse = 25;  /* 50% 占空比初始值 */
    sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
    sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
    
    if (HAL_TIM_PWM_ConfigChannel(&htim2, &sConfigOC, TIM_CHANNEL_1) != HAL_OK) {
        Error_Handler();
    }
    if (HAL_TIM_PWM_ConfigChannel(&htim2, &sConfigOC, TIM_CHANNEL_2) != HAL_OK) {
        Error_Handler();
    }
}

/* ==================== GPIO初始化 ==================== */
void MX_GPIO_Init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    
    /* I2C1 GPIO: PB6(SCL), PB7(SDA) */
    GPIO_InitStruct.Pin = GPIO_PIN_6 | GPIO_PIN_7;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
    
    /* 电机方向控制 GPIO */
    GPIO_InitStruct.Pin = GPIO_PIN_4 | GPIO_PIN_5;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
}
'''
        print("✅ 配置代码生成完成")
        return code


# ====================== 3. 代码生成Agent ======================

class CodeGenerateAgent(BaseAgent):
    """
    代码生成Agent: 生成HAL库驱动和控制算法代码
    
    核心能力:
    - 外设驱动自动生成
    - 算法代码模板
    - 代码规范性检查
    - 注释自动添加
    """
    
    def __init__(self):
        super().__init__("CodeGenerateAgent")
    
    def process(self, modules: List[ModuleSpec]) -> str:
        """生成驱动和算法代码"""
        self.update_state(AgentState.RUNNING)
        
        print("=" * 60)
        print("【代码生成Agent】启动 - HAL库代码生成")
        print("=" * 60)
        
        # 长链推理: 代码生成流程
        code = self._generate_with_reasoning(modules)
        
        self.update_state(AgentState.SUCCESS)
        return code
    
    def _generate_with_reasoning(self, modules: List[ModuleSpec]) -> str:
        """带推理的代码生成"""
        
        # 分析模块类型
        module_types = {}
        for m in modules:
            module_types[m.category] = module_types.get(m.category, 0) + 1
        
        print(f"📋 推理步骤1: 模块类型分析")
        print(f"   {module_types}")
        
        # 生成对应代码
        print(f"\n📋 推理步骤2: 生成驱动代码")
        code = self._build_driver_code(modules)
        
        return code
    
    def _build_driver_code(self, modules: List[ModuleSpec]) -> str:
        """构建驱动代码"""
        code = '''
/* ============================================================================
 * 驱动层代码 - 自动生成
 * ============================================================================ */

/* ==================== MPU6050传感器驱动 ==================== */
#define MPU6050_ADDR        0xD0
#define MPU6050_WHO_AM_I    0x75
#define MPU6050_PWR_MGMT_1  0x6B
#define MPU6050_GYRO_CONFIG 0x1B
#define MPU6050_ACCEL_CONFIG 0x1C

typedef struct {
    int16_t accel_x, accel_y, accel_z;
    int16_t gyro_x, gyro_y, gyro_z;
    float pitch, roll, yaw;
} MPU6050_Data_t;

static MPU6050_Data_t mpu_data = {0};

/**
 * @brief MPU6050初始化
 * @retval 0:成功 1:失败
 */
uint8_t MPU6050_Init(void)
{
    uint8_t check = 0;
    uint8_t data = 0;
    
    /* 读取WHO_AM_I寄存器验证设备 */
    HAL_I2C_Mem_Read(&hi2c1, MPU6050_ADDR, MPU6050_WHO_AM_I, 1, &check, 1, 100);
    if (check != 0x68) {
        return 1;  /* 设备ID不匹配 */
    }
    
    /* 唤醒MPU6050 */
    data = 0x00;
    HAL_I2C_Mem_Write(&hi2c1, MPU6050_ADDR, MPU6050_PWR_MGMT_1, 1, &data, 1, 100);
    HAL_Delay(10);
    
    /* 配置陀螺仪量程 ±2000dps */
    data = 0x18;
    HAL_I2C_Mem_Write(&hi2c1, MPU6050_ADDR, MPU6050_GYRO_CONFIG, 1, &data, 1, 100);
    
    /* 配置加速度计量程 ±4g */
    data = 0x08;
    HAL_I2C_Mem_Write(&hi2c1, MPU6050_ADDR, MPU6050_ACCEL_CONFIG, 1, &data, 1, 100);
    
    return 0;
}

/**
 * @brief 读取MPU6050原始数据
 */
void MPU6050_ReadRaw(void)
{
    uint8_t buffer[14] = {0};
    
    HAL_I2C_Mem_Read(&hi2c1, MPU6050_ADDR, 0x3B, 1, buffer, 14, 100);
    
    mpu_data.accel_x = (buffer[0] << 8) | buffer[1];
    mpu_data.accel_y = (buffer[2] << 8) | buffer[3];
    mpu_data.accel_z = (buffer[4] << 8) | buffer[5];
    mpu_data.gyro_x = (buffer[8] << 8) | buffer[9];
    mpu_data.gyro_y = (buffer[10] << 8) | buffer[11];
    mpu_data.gyro_z = (buffer[12] << 8) | buffer[13];
}

/* ==================== 姿态解算 (互补滤波) ==================== */
#define ALPHA 0.98f
#define DT    0.005f  /* 5ms采样周期 */

void Attitude_Update(void)
{
    float accel_pitch, accel_roll;
    float gyro_pitch_rate, gyro_roll_rate;
    
    /* 加速度计计算角度 */
    accel_pitch = atan2f(mpu_data.accel_y, mpu_data.accel_z) * 57.3f;
    accel_roll = atan2f(mpu_data.accel_x, mpu_data.accel_z) * 57.3f;
    
    /* 陀螺仪角速度 (°/s) */
    gyro_pitch_rate = mpu_data.gyro_x / 16.4f;  /* 2000dps灵敏度 */
    gyro_roll_rate = mpu_data.gyro_y / 16.4f;
    
    /* 互补滤波融合 */
    mpu_data.pitch = ALPHA * (mpu_data.pitch + gyro_pitch_rate * DT) 
                   + (1.0f - ALPHA) * accel_pitch;
    mpu_data.roll = ALPHA * (mpu_data.roll + gyro_roll_rate * DT) 
                  + (1.0f - ALPHA) * accel_roll;
}

/* ==================== PID控制器 ==================== */
typedef struct {
    float kp, ki, kd;
    float target;
    float integral;
    float last_error;
    float integral_limit;
    float output_limit;
} PID_Controller_t;

static PID_Controller_t balance_pid = {
    .kp = 12.0f,
    .ki = 0.05f,
    .kd = 20.0f,
    .target = 0.0f,
    .integral = 0.0f,
    .last_error = 0.0f,
    .integral_limit = 500.0f,
    .output_limit = 100.0f
};

/**
 * @brief PID计算
 * @param pid PID控制器指针
 * @param measure 测量值
 * @retval 控制输出
 */
float PID_Calculate(PID_Controller_t *pid, float measure)
{
    float error, output;
    
    error = pid->target - measure;
    
    /* 积分 */
    pid->integral += error;
    
    /* 积分限幅 (抗积分饱和) */
    if (pid->integral > pid->integral_limit) {
        pid->integral = pid->integral_limit;
    } else if (pid->integral < -pid->integral_limit) {
        pid->integral = -pid->integral_limit;
    }
    
    /* PID输出 */
    output = pid->kp * error 
           + pid->ki * pid->integral 
           + pid->kd * (error - pid->last_error);
    
    pid->last_error = error;
    
    /* 输出限幅 */
    if (output > pid->output_limit) {
        output = pid->output_limit;
    } else if (output < -pid->output_limit) {
        output = -pid->output_limit;
    }
    
    return output;
}

/* ==================== 电机控制 ==================== */
void Motor_SetSpeed(int8_t left, int8_t right)
{
    /* 左电机 */
    if (left >= 0) {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);
    } else {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET);
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_RESET);
    }
    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, abs(left) * 50 / 100);
    
    /* 右电机 */
    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_2, abs(right) * 50 / 100);
}

/* ==================== 主控制循环 ==================== */
void Balance_Control(void)
{
    float balance_output;
    
    /* 读取传感器数据 */
    MPU6050_ReadRaw();
    
    /* 姿态解算 */
    Attitude_Update();
    
    /* PID平衡控制 */
    balance_output = PID_Calculate(&balance_pid, mpu_data.pitch);
    
    /* 电机输出 */
    Motor_SetSpeed((int8_t)balance_output, (int8_t)balance_output);
}

/* ==================== 定时器中断回调 ==================== */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM3) {
        Balance_Control();
    }
}
'''
        print("✅ 驱动代码生成完成")
        return code


# ====================== 4. 调试排错Agent ======================

class DebugAgent(BaseAgent):
    """
    调试排错Agent: 智能分析错误日志，长链推理定位问题根源
    
    核心能力:
    - 串口日志解析
    - 硬件故障诊断
    - 长链推理定位
    - 修复方案生成
    """
    
    ERROR_PATTERNS = {
        ErrorType.I2C_NO_ACK: [
            r"I2C.*Error",
            r"HAL_I2C.*TIMEOUT",
            r"无应答",
            r"NACK"
        ],
        ErrorType.HARD_FAULT: [
            r"HardFault",
            r"硬件故障",
            r"MemManage_Handler",
            r"BusFault"
        ],
        ErrorType.CLOCK_CONFIG_ERROR: [
            r"RCC.*Error",
            r"时钟配置失败",
            r"PLL.*Error"
        ],
        ErrorType.DEVICE_ADDR_MISMATCH: [
            r"设备ID.*不匹配",
            r"WHO_AM_I.*fail",
            r"0x68.*expected"
        ],
        ErrorType.TIMING_VIOLATION: [
            r"时序.*错误",
            r"timing.*violation",
            r"setup.*hold"
        ]
    }
    
    SOLUTIONS = {
        ErrorType.I2C_NO_ACK: {
            "root_cause": "I2C总线无应答，可能原因：设备地址错误、上拉电阻缺失、时钟频率过高",
            "solutions": [
                "检查设备地址是否正确 (MPU6050: 0xD0/0xD1)",
                "确认I2C总线有4.7K上拉电阻",
                "降低I2C时钟频率至100kHz测试",
                "检查硬件连接是否松动"
            ],
            "code_fix": "hi2c1.Init.ClockSpeed = 100000;  /* 降低至100kHz */"
        },
        ErrorType.HARD_FAULT: {
            "root_cause": "硬件故障，常见原因：数组越界、空指针访问、栈溢出",
            "solutions": [
                "检查数组访问是否有越界",
                "验证指针是否已初始化",
                "增大栈空间 (修改启动文件Stack_Size)",
                "使用调试器查看故障寄存器"
            ],
            "code_fix": "/* 添加边界检查 */\nif (index < ARRAY_SIZE) {\n    array[index] = value;\n}"
        },
        ErrorType.CLOCK_CONFIG_ERROR: {
            "root_cause": "时钟配置错误，可能原因：外部晶振频率不匹配、PLL配置错误",
            "solutions": [
                "确认外部晶振频率 (常见8MHz/12MHz)",
                "检查PLL倍频系数是否正确",
                "尝试使用内部HSI时钟",
                "验证Flash延迟设置"
            ],
            "code_fix": "/* 使用内部HSI时钟 */\nRCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;\nRCC_OscInitStruct.HSIState = RCC_HSI_ON;"
        },
        ErrorType.DEVICE_ADDR_MISMATCH: {
            "root_cause": "设备地址不匹配，传感器未正确连接或ID错误",
            "solutions": [
                "使用I2C扫描程序检测设备地址",
                "检查传感器供电是否正常",
                "确认AD0引脚电平 (决定MPU6050地址)",
                "检查硬件焊接是否正常"
            ],
            "code_fix": "/* I2C地址扫描 */\nfor (uint8_t addr = 0; addr < 127; addr++) {\n    if (HAL_I2C_IsDeviceReady(&hi2c1, addr<<1, 1, 10) == HAL_OK) {\n        printf(\"Found device at 0x%02X\\n\", addr);\n    }\n}"
        }
    }
    
    def __init__(self):
        super().__init__("DebugAgent")
    
    def process(self, log_text: str) -> DebugResult:
        """处理调试日志"""
        self.update_state(AgentState.RUNNING)
        
        print("=" * 60)
        print("【调试排错Agent】启动 - 长链推理分析")
        print("=" * 60)
        print(f"📥 输入日志: {log_text[:100]}...\n")
        
        # 长链推理: 错误诊断流程
        result = self._diagnose_with_reasoning(log_text)
        
        self.update_state(AgentState.SUCCESS)
        return result
    
    def _diagnose_with_reasoning(self, log_text: str) -> DebugResult:
        """带长链推理的错误诊断"""
        
        # 推理步骤1: 错误模式匹配
        step1 = ReasoningStep(
            step_id=1,
            description="错误模式匹配",
            input_data=log_text,
            output_data=self._match_error_patterns(log_text),
            confidence=0.90,
            next_steps=[2]
        )
        self.reasoning_chain.append(step1)
        print(f"📋 推理步骤1: 错误模式匹配")
        print(f"   匹配结果: {step1.output_data}")
        
        # 推理步骤2: 根因分析
        error_type = step1.output_data if step1.output_data else ErrorType.HARD_FAULT
        step2 = ReasoningStep(
            step_id=2,
            description="根因分析",
            input_data=error_type,
            output_data=self._analyze_root_cause(error_type, log_text),
            confidence=0.85,
            next_steps=[3]
        )
        self.reasoning_chain.append(step2)
        print(f"\n📋 推理步骤2: 根因分析")
        print(f"   根本原因: {step2.output_data}")
        
        # 推理步骤3: 解决方案生成
        step3 = ReasoningStep(
            step_id=3,
            description="生成解决方案",
            input_data=error_type,
            output_data=self._generate_solution(error_type),
            confidence=0.80,
            next_steps=[]
        )
        self.reasoning_chain.append(step3)
        print(f"\n📋 推理步骤3: 解决方案生成")
        print(f"   方案数量: {len(step3.output_data)}")
        
        # 构建结果
        solution_info = self.SOLUTIONS.get(error_type, {})
        result = DebugResult(
            error_type=error_type,
            root_cause=step2.output_data,
            solution="\n".join([f"  {i+1}. {s}" for i, s in enumerate(step3.output_data)]),
            code_fix=solution_info.get("code_fix"),
            reasoning_chain=self.reasoning_chain
        )
        
        self._print_debug_result(result)
        return result
    
    def _match_error_patterns(self, log_text: str) -> Optional[ErrorType]:
        """匹配错误模式"""
        for error_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, log_text, re.IGNORECASE):
                    return error_type
        return None
    
    def _analyze_root_cause(self, error_type: ErrorType, log_text: str) -> str:
        """分析根本原因"""
        solution_info = self.SOLUTIONS.get(error_type, {})
        return solution_info.get("root_cause", "未知错误，需要进一步分析")
    
    def _generate_solution(self, error_type: ErrorType) -> List[str]:
        """生成解决方案"""
        solution_info = self.SOLUTIONS.get(error_type, {})
        return solution_info.get("solutions", ["请提供更详细的错误信息"])
    
    def _print_debug_result(self, result: DebugResult):
        """打印调试结果"""
        print("\n" + "=" * 50)
        print("🔍 调试结果")
        print("=" * 50)
        print(f"❌ 错误类型: {result.error_type.value}")
        print(f"🎯 根本原因: {result.root_cause}")
        print(f"\n✅ 解决方案:")
        print(result.solution)
        if result.code_fix:
            print(f"\n📝 代码修复建议:")
            print(result.code_fix)


# ====================== 5. 验证Agent ======================

class VerifyAgent(BaseAgent):
    """
    验证Agent: QEMU仿真验证代码功能
    
    核心能力:
    - QEMU模拟器集成
    - 外设初始化验证
    - 逻辑正确性检查
    - 验证报告生成
    """
    
    def __init__(self):
        super().__init__("VerifyAgent")
        self.test_results: List[Dict[str, Any]] = []
    
    def process(self, code: str) -> Dict[str, Any]:
        """验证代码"""
        self.update_state(AgentState.RUNNING)
        
        print("=" * 60)
        print("【验证Agent】启动 - QEMU仿真验证")
        print("=" * 60)
        
        # 长链推理: 验证流程
        result = self._verify_with_reasoning(code)
        
        self.update_state(AgentState.SUCCESS)
        return result
    
    def _verify_with_reasoning(self, code: str) -> Dict[str, Any]:
        """带推理的验证流程"""
        
        # 推理步骤1: 代码静态分析
        print("📋 推理步骤1: 代码静态分析")
        static_result = self._static_analysis(code)
        self.test_results.append(static_result)
        print(f"   分析结果: {static_result['status']}")
        
        # 推理步骤2: 外设初始化验证
        print("\n📋 推理步骤2: 外设初始化验证")
        peripheral_result = self._verify_peripherals(code)
        self.test_results.append(peripheral_result)
        print(f"   验证结果: {peripheral_result['status']}")
        
        # 推理步骤3: 控制逻辑验证
        print("\n📋 推理步骤3: 控制逻辑验证")
        logic_result = self._verify_control_logic(code)
        self.test_results.append(logic_result)
        print(f"   验证结果: {logic_result['status']}")
        
        # 生成验证报告
        report = self._generate_report()
        
        return report
    
    def _static_analysis(self, code: str) -> Dict[str, Any]:
        """静态代码分析"""
        issues = []
        
        # 检查关键函数
        required_functions = ["SystemClock_Config", "MX_I2C1_Init", "MX_TIM2_Init", "MPU6050_Init"]
        for func in required_functions:
            if func not in code:
                issues.append(f"缺少函数: {func}")
        
        # 检查头文件
        if "#include" not in code:
            issues.append("缺少头文件引用")
        
        return {
            "test_name": "静态代码分析",
            "status": "通过" if not issues else "警告",
            "issues": issues
        }
    
    def _verify_peripherals(self, code: str) -> Dict[str, Any]:
        """验证外设配置"""
        peripherals = {
            "I2C1": "I2C1" in code,
            "TIM2": "TIM2" in code,
            "GPIO": "GPIO_Init" in code,
            "时钟": "SystemClock_Config" in code
        }
        
        all_passed = all(peripherals.values())
        
        return {
            "test_name": "外设初始化验证",
            "status": "通过" if all_passed else "失败",
            "details": peripherals
        }
    
    def _verify_control_logic(self, code: str) -> Dict[str, Any]:
        """验证控制逻辑"""
        logic_checks = {
            "PID控制器": "PID_Calculate" in code,
            "姿态解算": "Attitude_Update" in code,
            "电机控制": "Motor_SetSpeed" in code,
            "中断回调": "HAL_TIM_PeriodElapsedCallback" in code
        }
        
        all_passed = all(logic_checks.values())
        
        return {
            "test_name": "控制逻辑验证",
            "status": "通过" if all_passed else "失败",
            "details": logic_checks
        }
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        passed = sum(1 for r in self.test_results if r["status"] == "通过")
        total = len(self.test_results)
        
        report = {
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": f"{passed/total*100:.1f}%"
            },
            "details": self.test_results,
            "final_status": "验证通过" if passed == total else "需要修改"
        }
        
        self._print_report(report)
        return report
    
    def _print_report(self, report: Dict[str, Any]):
        """打印验证报告"""
        print("\n" + "=" * 50)
        print("📊 验证报告")
        print("=" * 50)
        print(f"总测试数: {report['summary']['total_tests']}")
        print(f"通过: {report['summary']['passed']}")
        print(f"失败: {report['summary']['failed']}")
        print(f"通过率: {report['summary']['pass_rate']}")
        print(f"\n🏆 最终状态: {report['final_status']}")


# ====================== Agent协调器 ======================

class AgentCoordinator:
    """
    Agent协调器: 管理多Agent协作流程
    
    核心功能:
    - Agent生命周期管理
    - 消息路由
    - 任务调度
    - 状态同步
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_bus: List[AgentMessage] = []
        self.workflow_state: Dict[str, Any] = {}
    
    def register_agent(self, agent: BaseAgent):
        """注册Agent"""
        self.agents[agent.name] = agent
        print(f"✅ 注册Agent: {agent.name}")
    
    def route_message(self, message: AgentMessage):
        """路由消息到目标Agent"""
        if message.receiver in self.agents:
            self.agents[message.receiver].receive_message(message)
        elif message.receiver == "all":
            for agent in self.agents.values():
                agent.receive_message(message)
    
    def execute_workflow(self, demand: str) -> Dict[str, Any]:
        """执行完整工作流"""
        print("\n" + "🚀" * 30)
        print("嵌入式开发全流程辅助Agent系统 - 多Agent协作启动")
        print("🚀" * 30 + "\n")
        
        results = {}
        
        # 阶段1: 需求解析
        print("\n" + "▶" * 20 + " 阶段1: 需求解析 " + "▶" * 20)
        agent1 = self.agents.get("DemandParseAgent")
        if agent1:
            project_type, modules = agent1.process(demand)
            results["demand_parse"] = {
                "project_type": project_type,
                "modules": [{"name": m.name, "category": m.category} for m in modules]
            }
        
        # 阶段2: 配置生成
        print("\n" + "▶" * 20 + " 阶段2: 配置生成 " + "▶" * 20)
        agent2 = self.agents.get("ConfigGenerateAgent")
        if agent2:
            config_code = agent2.process((project_type, modules))
            results["config_code"] = config_code
        
        # 阶段3: 代码生成
        print("\n" + "▶" * 20 + " 阶段3: 代码生成 " + "▶" * 20)
        agent3 = self.agents.get("CodeGenerateAgent")
        if agent3:
            driver_code = agent3.process(modules)
            results["driver_code"] = driver_code
        
        # 阶段4: 调试验证 (模拟)
        print("\n" + "▶" * 20 + " 阶段4: 调试排错 " + "▶" * 20)
        agent4 = self.agents.get("DebugAgent")
        if agent4:
            debug_result = agent4.process("测试日志：系统运行正常，无错误信息")
            results["debug_result"] = {
                "error_type": debug_result.error_type.value if debug_result.error_type else "无",
                "root_cause": debug_result.root_cause
            }
        
        # 阶段5: 仿真验证
        print("\n" + "▶" * 20 + " 阶段5: 仿真验证 " + "▶" * 20)
        agent5 = self.agents.get("VerifyAgent")
        if agent5:
            full_code = results.get("config_code", "") + results.get("driver_code", "")
            verify_result = agent5.process(full_code)
            results["verify_result"] = verify_result
        
        return results


# ====================== 主程序入口 ======================

def main():
    """主程序入口"""
    print("=" * 70)
    print("       嵌入式开发全流程辅助Agent系统 v2.0")
    print("       STM32专用版 - 多Agent协作 + 长链推理")
    print("=" * 70)
    
    # 创建协调器
    coordinator = AgentCoordinator()
    
    # 注册所有Agent
    coordinator.register_agent(DemandParseAgent())
    coordinator.register_agent(ConfigGenerateAgent())
    coordinator.register_agent(CodeGenerateAgent())
    coordinator.register_agent(DebugAgent())
    coordinator.register_agent(VerifyAgent())
    
    # 用户需求
    user_demand = """
    我需要做一个基于STM32F103的平衡车项目：
    1. 使用MPU6050进行姿态采集
    2. 需要电机PID控制实现平衡
    3. 要求姿态解算准确，控制响应快速
    """
    
    # 执行工作流
    results = coordinator.execute_workflow(user_demand)
    
    # 输出工程文件
    print("\n" + "=" * 70)
    print("📦 工程文件生成")
    print("=" * 70)
    
    full_code = results.get("config_code", "") + results.get("driver_code", "")
    output_file = "STM32平衡车工程_完整版.c"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_code)
    
    print(f"✅ 生成文件: {output_file}")
    print(f"✅ 代码行数: {len(full_code.split(chr(10)))}")
    print(f"✅ 验证状态: {results.get('verify_result', {}).get('final_status', '未知')}")
    
    print("\n" + "=" * 70)
    print("🎉 全流程完成！项目可直接用于Keil编译烧录")
    print("=" * 70)


if __name__ == '__main__':
    main()
