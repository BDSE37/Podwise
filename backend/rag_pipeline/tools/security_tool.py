#!/usr/bin/env python3
"""
Podwise RAG Pipeline - 安全工具模組

整合 Guardrails AI 提供多種安全驗證器：
- 毒性內容檢測 (Toxic Content)
- 自殘內容檢測 (Self-Harm)
- 個人資訊保護 (PII Protection)
- 惡意程式碼檢測 (Malicious Code)
- 不當內容過濾 (Inappropriate Content)

支援 LangChain、CrewAI、FastAPI Pipeline 整合
遵循 OOP 設計模式和 Google Clean Code 原則

作者: Podwise Team
版本: 1.0.0
授權: MIT
"""

import os
import sys
import logging
import json
import re
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from functools import wraps
from enum import Enum
import asyncio
from datetime import datetime

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from guardrails import Guard
    from guardrails.validators import (
        ToxicLanguage, 
        SelfHarm, 
        PII, 
        MaliciousCode,
        InappropriateContent,
        ValidLength,
        ValidChoices,
        ValidRange,
        ValidFormat
    )
    GUARDRAILS_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Guardrails AI 未安裝，將使用基本驗證器")
    GUARDRAILS_AVAILABLE = False


class SecurityLevel(Enum):
    """安全等級枚舉"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityConfig:
    """安全配置類別"""
    # 啟用驗證器
    enable_toxic_detection: bool = True
    enable_self_harm_detection: bool = True
    enable_pii_protection: bool = True
    enable_malicious_code_detection: bool = True
    enable_inappropriate_content_detection: bool = True
    
    # 安全等級
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    
    # 驗證參數
    max_length: int = 10000
    min_length: int = 1
    
    # 錯誤處理
    raise_on_violation: bool = False
    log_violations: bool = True
    
    # 自定義規則
    custom_patterns: List[str] = field(default_factory=list)
    blocked_keywords: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """驗證結果類別"""
    is_valid: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    confidence_score: float = 1.0
    processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class BaseSecurityValidator:
    """基礎安全驗證器"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate(self, content: str) -> ValidationResult:
        """基礎驗證方法"""
        start_time = datetime.now()
        violations = []
        warnings = []
        
        try:
            # 基本長度檢查
            if len(content) < self.config.min_length:
                violations.append(f"內容長度過短 ({len(content)} < {self.config.min_length})")
            
            if len(content) > self.config.max_length:
                violations.append(f"內容長度過長 ({len(content)} > {self.config.max_length})")
            
            # 自定義關鍵字檢查
            for keyword in self.config.blocked_keywords:
                if keyword.lower() in content.lower():
                    violations.append(f"包含被封鎖關鍵字: {keyword}")
            
            # 自定義模式檢查
            for pattern in self.config.custom_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    violations.append(f"符合封鎖模式: {pattern}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ValidationResult(
                is_valid=len(violations) == 0,
                violations=violations,
                warnings=warnings,
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"驗證過程發生錯誤: {e}")
            return ValidationResult(
                is_valid=False,
                violations=[f"驗證錯誤: {str(e)}"],
                processing_time=(datetime.now() - start_time).total_seconds()
            )


class GuardrailsSecurityValidator(BaseSecurityValidator):
    """Guardrails AI 安全驗證器"""
    
    def __init__(self, config: SecurityConfig):
        super().__init__(config)
        self.guard = None
        self._initialize_guard()
    
    def _initialize_guard(self):
        """初始化 Guardrails 驗證器"""
        if not GUARDRAILS_AVAILABLE:
            self.logger.warning("Guardrails AI 不可用，使用基本驗證器")
            return
        
        try:
            validators = []
            
            # 毒性內容檢測
            if self.config.enable_toxic_detection:
                validators.append(ToxicLanguage())
            
            # 自殘內容檢測
            if self.config.enable_self_harm_detection:
                validators.append(SelfHarm())
            
            # 個人資訊保護
            if self.config.enable_pii_protection:
                validators.append(PII())
            
            # 惡意程式碼檢測
            if self.config.enable_malicious_code_detection:
                validators.append(MaliciousCode())
            
            # 不當內容檢測
            if self.config.enable_inappropriate_content_detection:
                validators.append(InappropriateContent())
            
            # 長度驗證
            validators.append(ValidLength(min_length=self.config.min_length, max_length=self.config.max_length))
            
            # 創建 Guard 實例
            self.guard = Guard.from_string(
                validators=validators,
                description="Podwise 安全內容驗證"
            )
            
            self.logger.info("✅ Guardrails AI 驗證器初始化成功")
            
        except Exception as e:
            self.logger.error(f"❌ Guardrails AI 初始化失敗: {e}")
            self.guard = None
    
    def validate(self, content: str) -> ValidationResult:
        """使用 Guardrails AI 進行驗證"""
        start_time = datetime.now()
        
        # 先執行基礎驗證
        base_result = super().validate(content)
        if not base_result.is_valid:
            return base_result
        
        # 如果 Guardrails 不可用，返回基礎驗證結果
        if self.guard is None:
            return base_result
        
        try:
            # 使用 Guardrails 進行驗證
            validation_result = self.guard.validate(content)
            
            violations = []
            warnings = []
            
            # 檢查驗證結果
            if validation_result.validation_passed:
                is_valid = True
            else:
                is_valid = False
                for error in validation_result.validation_errors:
                    violations.append(f"Guardrails 驗證失敗: {error}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = ValidationResult(
                is_valid=is_valid,
                violations=violations,
                warnings=warnings,
                processing_time=processing_time
            )
            
            # 記錄違規
            if self.config.log_violations and not result.is_valid:
                self.logger.warning(f"安全違規檢測: {violations}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Guardrails 驗證錯誤: {e}")
            return ValidationResult(
                is_valid=False,
                violations=[f"Guardrails 驗證錯誤: {str(e)}"],
                processing_time=(datetime.now() - start_time).total_seconds()
            )


class SecurityTool:
    """Podwise 安全工具主類別"""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.validator = GuardrailsSecurityValidator(self.config)
        self.logger = logging.getLogger(__name__)
        
        # 統計資訊
        self.stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "total_violations": 0,
            "total_processing_time": 0.0
        }
    
    def validate_content(self, content: str) -> ValidationResult:
        """驗證內容安全性"""
        self.stats["total_validations"] += 1
        
        result = self.validator.validate(content)
        
        if result.is_valid:
            self.stats["passed_validations"] += 1
        else:
            self.stats["failed_validations"] += 1
            self.stats["total_violations"] += len(result.violations)
        
        self.stats["total_processing_time"] += result.processing_time
        
        return result
    
    def validate_batch(self, contents: List[str]) -> List[ValidationResult]:
        """批次驗證內容"""
        results = []
        for content in contents:
            results.append(self.validate_content(content))
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取驗證統計資訊"""
        return {
            **self.stats,
            "average_processing_time": (
                self.stats["total_processing_time"] / self.stats["total_validations"]
                if self.stats["total_validations"] > 0 else 0
            ),
            "success_rate": (
                self.stats["passed_validations"] / self.stats["total_validations"]
                if self.stats["total_validations"] > 0 else 0
            )
        }
    
    def reset_stats(self):
        """重置統計資訊"""
        self.stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "total_violations": 0,
            "total_processing_time": 0.0
        }


# 裝飾器函數
def security_check(
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
    raise_on_violation: bool = False
):
    """安全檢查裝飾器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 創建安全工具實例
            config = SecurityConfig(
                security_level=security_level,
                raise_on_violation=raise_on_violation
            )
            security_tool = SecurityTool(config)
            
            # 檢查輸入參數
            for arg in args:
                if isinstance(arg, str):
                    result = security_tool.validate_content(arg)
                    if not result.is_valid and raise_on_violation:
                        raise ValueError(f"安全驗證失敗: {result.violations}")
            
            for key, value in kwargs.items():
                if isinstance(value, str):
                    result = security_tool.validate_content(value)
                    if not result.is_valid and raise_on_violation:
                        raise ValueError(f"安全驗證失敗: {result.violations}")
            
            # 執行原函數
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def async_security_check(
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
    raise_on_violation: bool = False
):
    """非同步安全檢查裝飾器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 創建安全工具實例
            config = SecurityConfig(
                security_level=security_level,
                raise_on_violation=raise_on_violation
            )
            security_tool = SecurityTool(config)
            
            # 檢查輸入參數
            for arg in args:
                if isinstance(arg, str):
                    result = security_tool.validate_content(arg)
                    if not result.is_valid and raise_on_violation:
                        raise ValueError(f"安全驗證失敗: {result.violations}")
            
            for key, value in kwargs.items():
                if isinstance(value, str):
                    result = security_tool.validate_content(value)
                    if not result.is_valid and raise_on_violation:
                        raise ValueError(f"安全驗證失敗: {result.violations}")
            
            # 執行原函數
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# FastAPI 整合
class FastAPISecurityMiddleware:
    """FastAPI 安全中間件"""
    
    def __init__(self, security_tool: SecurityTool):
        self.security_tool = security_tool
        self.logger = logging.getLogger(__name__)
    
    async def __call__(self, request, call_next):
        # 檢查請求內容
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    content = body.decode('utf-8')
                    result = self.security_tool.validate_content(content)
                    
                    if not result.is_valid:
                        self.logger.warning(f"請求內容安全違規: {result.violations}")
                        return JSONResponse(
                            status_code=400,
                            content={
                                "error": "安全驗證失敗",
                                "violations": result.violations,
                                "message": "請求內容包含不安全的內容"
                            }
                        )
            except Exception as e:
                self.logger.error(f"安全檢查錯誤: {e}")
        
        response = await call_next(request)
        return response


# LangChain 整合
class LangChainSecurityValidator:
    """LangChain 安全驗證器"""
    
    def __init__(self, security_tool: SecurityTool):
        self.security_tool = security_tool
        self.logger = logging.getLogger(__name__)
    
    def validate_prompt(self, prompt: str) -> bool:
        """驗證 LangChain 提示詞"""
        result = self.security_tool.validate_content(prompt)
        return result.is_valid
    
    def validate_response(self, response: str) -> bool:
        """驗證 LangChain 回應"""
        result = self.security_tool.validate_content(response)
        return result.is_valid


# CrewAI 整合
class CrewAISecurityValidator:
    """CrewAI 安全驗證器"""
    
    def __init__(self, security_tool: SecurityTool):
        self.security_tool = security_tool
        self.logger = logging.getLogger(__name__)
    
    def validate_agent_input(self, input_data: str) -> bool:
        """驗證 CrewAI 代理輸入"""
        result = self.security_tool.validate_content(input_data)
        return result.is_valid
    
    def validate_agent_output(self, output_data: str) -> bool:
        """驗證 CrewAI 代理輸出"""
        result = self.security_tool.validate_content(output_data)
        return result.is_valid


# 工廠函數
def create_security_tool(
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
    **kwargs
) -> SecurityTool:
    """創建安全工具實例"""
    config = SecurityConfig(security_level=security_level, **kwargs)
    return SecurityTool(config)


def create_fastapi_middleware(
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
    **kwargs
) -> FastAPISecurityMiddleware:
    """創建 FastAPI 安全中間件"""
    security_tool = create_security_tool(security_level, **kwargs)
    return FastAPISecurityMiddleware(security_tool)


def create_langchain_validator(
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
    **kwargs
) -> LangChainSecurityValidator:
    """創建 LangChain 安全驗證器"""
    security_tool = create_security_tool(security_level, **kwargs)
    return LangChainSecurityValidator(security_tool)


def create_crewai_validator(
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
    **kwargs
) -> CrewAISecurityValidator:
    """創建 CrewAI 安全驗證器"""
    security_tool = create_security_tool(security_level, **kwargs)
    return CrewAISecurityValidator(security_tool)


# 使用範例
if __name__ == "__main__":
    # 創建安全工具
    security_tool = create_security_tool(
        security_level=SecurityLevel.HIGH,
        blocked_keywords=["惡意", "攻擊", "病毒"],
        custom_patterns=[r"<script>.*</script>", r"javascript:"]
    )
    
    # 測試驗證
    test_content = "這是一個正常的測試內容"
    result = security_tool.validate_content(test_content)
    print(f"驗證結果: {result.is_valid}")
    print(f"違規項目: {result.violations}")
    print(f"處理時間: {result.processing_time:.4f}秒")
    
    # 測試統計
    stats = security_tool.get_stats()
    print(f"統計資訊: {stats}")
