"""
Solana Wallet Analyzer Service
Analyzes Solana wallets to determine if they're worth copy trading
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import httpx

# Set up logging
logger = logging.getLogger(__name__)

# Monkey patch to fix httpx compatibility issue
# TODO: Remove this workaround when solana library supports httpx>=0.25.0
# Currently needed for: solana 0.30.x-0.36.x with httpx>=0.25.0
# The solana library passes 'proxy' but httpx 0.25+ expects 'proxies'
_original_httpx_async_client_init = httpx.AsyncClient.__init__

def _patched_httpx_async_client_init(self, *args, proxy=None, **kwargs):
    """Patched init that converts 'proxy' to 'proxies' for compatibility"""
    if proxy is not None and 'proxies' not in kwargs:
        kwargs['proxies'] = proxy
    _original_httpx_async_client_init(self, *args, **kwargs)

httpx.AsyncClient.__init__ = _patched_httpx_async_client_init

# Now import solana modules
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey


class SolanaWalletAnalyzer:
    """Analyzes Solana wallet trading performance"""
    
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.client = AsyncClient(rpc_url)
        
    async def close(self):
        """Close the RPC client"""
        await self.client.close()
    
    async def get_wallet_balance(self, wallet_address: str) -> Optional[float]:
        """Get current SOL balance of wallet"""
        try:
            pubkey = Pubkey.from_string(wallet_address)
            response = await self.client.get_balance(pubkey)
            if response.value is not None:
                # Convert lamports to SOL (1 SOL = 1e9 lamports)
                return response.value / 1e9
            return None
        except Exception as e:
            logger.error(f"Error getting balance for {wallet_address}: {e}")
            return None
    
    async def get_transaction_signatures(
        self, 
        wallet_address: str, 
        limit: int = 100
    ) -> List[Dict]:
        """Get recent transaction signatures for a wallet"""
        try:
            pubkey = Pubkey.from_string(wallet_address)
            response = await self.client.get_signatures_for_address(
                pubkey, 
                limit=limit
            )
            if response.value:
                return response.value
            return []
        except Exception as e:
            logger.error(f"Error getting signatures for {wallet_address}: {e}")
            return []
    
    async def analyze_trading_activity(
        self, 
        wallet_address: str
    ) -> Dict:
        """
        Analyze wallet trading activity and performance
        Returns metrics like transaction count, volume, win rate, etc.
        """
        try:
            # Get transaction signatures
            signatures = await self.get_transaction_signatures(
                wallet_address, 
                limit=100
            )
            
            if not signatures:
                return {
                    "error": "No transactions found",
                    "valid": False
                }
            
            # Basic metrics
            total_transactions = len(signatures)
            
            # Calculate time range
            if signatures:
                latest_time = signatures[0].get('blockTime', 0)
                oldest_time = signatures[-1].get('blockTime', 0)
                
                if latest_time and oldest_time:
                    time_range_days = (latest_time - oldest_time) / 86400
                else:
                    time_range_days = 0
            else:
                time_range_days = 0
            
            # Get current balance
            balance = await self.get_wallet_balance(wallet_address)
            
            # Calculate activity metrics
            transactions_per_day = (
                total_transactions / time_range_days 
                if time_range_days > 0 
                else 0
            )
            
            return {
                "wallet_address": wallet_address,
                "total_transactions": total_transactions,
                "time_range_days": round(time_range_days, 2),
                "transactions_per_day": round(transactions_per_day, 2),
                "current_balance_sol": balance,
                "latest_transaction_time": (
                    datetime.fromtimestamp(signatures[0]['blockTime']).isoformat()
                    if signatures and signatures[0].get('blockTime')
                    else None
                ),
                "valid": True
            }
            
        except Exception as e:
            logger.error(f"Error analyzing wallet {wallet_address}: {e}")
            return {
                "error": str(e),
                "valid": False
            }
    
    def calculate_recommendation_score(self, metrics: Dict) -> Tuple[int, str]:
        """
        Calculate a recommendation score (0-100) based on wallet metrics
        Returns (score, recommendation_text)
        """
        if not metrics.get("valid"):
            return 0, "❌ Кошелек не найден или недействителен"
        
        score = 0
        reasons = []
        
        # Check transaction activity
        total_txs = metrics.get("total_transactions", 0)
        if total_txs > 50:
            score += 30
            reasons.append("✅ Высокая активность кошелька")
        elif total_txs > 20:
            score += 15
            reasons.append("⚠️ Средняя активность кошелька")
        else:
            reasons.append("❌ Низкая активность кошелька")
        
        # Check consistency
        txs_per_day = metrics.get("transactions_per_day", 0)
        if txs_per_day > 5:
            score += 25
            reasons.append("✅ Стабильная торговая активность")
        elif txs_per_day > 2:
            score += 10
            reasons.append("⚠️ Регулярная торговая активность")
        else:
            reasons.append("❌ Нерегулярная активность")
        
        # Check balance
        balance = metrics.get("current_balance_sol", 0)
        if balance and balance > 10:
            score += 25
            reasons.append("✅ Значительный баланс SOL")
        elif balance and balance > 1:
            score += 10
            reasons.append("⚠️ Средний баланс SOL")
        else:
            reasons.append("❌ Низкий баланс")
        
        # Check time range
        time_range = metrics.get("time_range_days", 0)
        if time_range > 30:
            score += 20
            reasons.append("✅ Долгая история торговли")
        elif time_range > 7:
            score += 10
            reasons.append("⚠️ Краткосрочная история")
        else:
            reasons.append("❌ Очень короткая история")
        
        # Generate recommendation
        if score >= 70:
            recommendation = "🟢 РЕКОМЕНДУЕТСЯ для копитрейдинга"
        elif score >= 40:
            recommendation = "🟡 СРЕДНЯЯ ПЕРСПЕКТИВНОСТЬ - требуется дополнительный анализ"
        else:
            recommendation = "🔴 НЕ РЕКОМЕНДУЕТСЯ для копитрейдинга"
        
        return score, f"{recommendation}\n\n" + "\n".join(reasons)
    
    async def generate_analysis_report(self, wallet_address: str) -> str:
        """Generate a comprehensive analysis report for a wallet"""
        try:
            # Analyze wallet
            metrics = await self.analyze_trading_activity(wallet_address)
            
            if not metrics.get("valid"):
                return f"❌ Ошибка анализа кошелька:\n{metrics.get('error', 'Неизвестная ошибка')}"
            
            # Calculate recommendation
            score, recommendation = self.calculate_recommendation_score(metrics)
            
            # Format report
            report = f"""
📊 **АНАЛИЗ SOLANA КОШЕЛЬКА**

🔑 Адрес: `{wallet_address[:8]}...{wallet_address[-8:]}`

📈 **МЕТРИКИ**:
• Всего транзакций: {metrics['total_transactions']}
• Период активности: {metrics['time_range_days']} дней
• Транзакций в день: {metrics['transactions_per_day']}
• Текущий баланс: {metrics['current_balance_sol']:.4f} SOL
• Последняя транзакция: {metrics.get('latest_transaction_time', 'N/A')}

⭐ **ОЦЕНКА**: {score}/100

🎯 **РЕКОМЕНДАЦИЯ**:
{recommendation}

⚠️ **ВНИМАНИЕ**: Это базовый анализ. Рекомендуется провести дополнительное исследование перед копитрейдингом.
"""
            return report.strip()
            
        except Exception as e:
            return f"❌ Ошибка при создании отчета: {str(e)}"
