//! Token query subcommand

use agentsight::{
    TimePeriod, TokenQueryResult, format_tokens_with_commas, Trend, TokenStore,
    TokenConsumptionStore, TokenConsumptionFilter, TokenConsumptionQueryResult,
    SqliteConfig,
};
use structopt::StructOpt;
use std::collections::HashMap;

/// Token query subcommand
#[derive(Debug, StructOpt, Clone)]
pub struct TokenCommand {
    /// Query by fixed time period
    #[structopt(long, possible_values = &["today", "yesterday", "week", "last_week", "month", "last_month"])]
    pub period: Option<String>,
    
    /// Query last N hours
    #[structopt(long)]
    pub hours: Option<u64>,
    
    /// Compare with previous period
    #[structopt(long)]
    pub compare: bool,
    
    /// Show breakdown by agent/task
    #[structopt(long)]
    pub breakdown: bool,

    /// Show token consumption detail (by_role, output_by_type, tools, system_prompt)
    #[structopt(long)]
    pub detail: bool,

    /// When --detail is set, also include the individual records in the output
    #[structopt(long)]
    pub records: bool,
    
    /// Output as JSON
    #[structopt(long)]
    pub json: bool,
    
    /// Custom data file path
    #[structopt(long)]
    pub data_file: Option<String>,
}

impl TokenCommand {
    pub fn execute(&self) {
        // Determine data file path
        // Use the unified database path (agentsight.db) as default,
        // which is where Storage writes all tables.
        let data_path = self.data_file
            .as_ref()
            .map(|p| std::path::PathBuf::from(p))
            .unwrap_or_else(|| SqliteConfig::default().db_path());
        
        if self.detail {
            self.execute_detail(&data_path);
        } else {
            self.execute_summary(&data_path);
        }
    }

    fn execute_summary(&self, data_path: &std::path::Path) {
        // Open token store
        let store = TokenStore::new(data_path);
        let query = agentsight::TokenQuery::new(&store);
        
        // Execute query
        let result = if let Some(hours) = self.hours {
            if self.compare && self.breakdown {
                let mut r = query.by_hours_with_compare(hours);
                r.breakdown = compute_breakdown_for_hours(&store, hours);
                r
            } else if self.compare {
                query.by_hours_with_compare(hours)
            } else if self.breakdown {
                let mut r = query.by_hours(hours);
                r.breakdown = compute_breakdown_for_hours(&store, hours);
                r
            } else {
                query.by_hours(hours)
            }
        } else if let Some(ref period_str) = self.period {
            let period = super::parse_period(period_str);
            if self.compare && self.breakdown {
                query.full_query(period)
            } else if self.compare {
                query.by_period_with_compare(period)
            } else if self.breakdown {
                query.by_period_with_breakdown(period)
            } else {
                query.by_period(period)
            }
        } else {
            if self.compare && self.breakdown {
                query.full_query(TimePeriod::Today)
            } else if self.compare {
                query.by_period_with_compare(TimePeriod::Today)
            } else if self.breakdown {
                query.by_period_with_breakdown(TimePeriod::Today)
            } else {
                query.by_period(TimePeriod::Today)
            }
        };
        
        // Output result
        if self.json {
            println!("{}", serde_json::to_string_pretty(&result).unwrap());
        } else {
            print_human_readable(&result, self.compare, self.breakdown);
        }
    }

    fn execute_detail(&self, data_path: &std::path::Path) {
        let store = match TokenConsumptionStore::new(data_path) {
            Ok(s) => s,
            Err(e) => {
                eprintln!("无法打开 token consumption 数据库: {}", e);
                return;
            }
        };

        // Build time filter
        let filter = if let Some(hours) = self.hours {
            let now = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_nanos() as u64)
                .unwrap_or(0);
            let start_ns = now.saturating_sub(hours * 3_600 * 1_000_000_000);
            TokenConsumptionFilter {
                start_ns: Some(start_ns),
                end_ns: Some(now),
                ..Default::default()
            }
        } else if let Some(ref period_str) = self.period {
            let period = super::parse_period(period_str);
            let (start_ns, end_ns) = period.time_range();
            TokenConsumptionFilter {
                start_ns: Some(start_ns),
                end_ns: Some(end_ns),
                ..Default::default()
            }
        } else {
            // Default: today
            let (start_ns, end_ns) = TimePeriod::Today.time_range();
            TokenConsumptionFilter {
                start_ns: Some(start_ns),
                end_ns: Some(end_ns),
                ..Default::default()
            }
        };

        let period_label = if let Some(hours) = self.hours {
            format!("最近 {} 小时", hours)
        } else if let Some(ref p) = self.period {
            super::parse_period(p).to_string()
        } else {
            TimePeriod::Today.to_string()
        };

        match store.aggregate(&filter, period_label, self.records) {
            Ok(result) => {
                if self.json {
                    println!("{}", serde_json::to_string_pretty(&result).unwrap());
                } else {
                    print_detail_human_readable(&result, self.records);
                }
            }
            Err(e) => eprintln!("查询失败: {}", e),
        }
    }
}

/// Compute breakdown for hours (helper)
fn compute_breakdown_for_hours(store: &TokenStore, hours: u64) -> Vec<agentsight::TokenBreakdown> {
    let records = store.by_last_hours(hours);
    let total_tokens: u64 = records.iter().map(|r| r.total_tokens()).sum();

    let mut agent_totals: HashMap<String, (u64, u64, u64, u64)> = HashMap::new();

    for record in records.iter() {
        let name = record.agent.as_ref().unwrap_or(&record.comm).clone();

        let entry = agent_totals.entry(name).or_insert((0, 0, 0, 0));
        entry.0 += record.total_tokens();
        entry.1 += record.input_tokens;
        entry.2 += record.output_tokens;
        entry.3 += 1;
    }

    let mut breakdown: Vec<agentsight::TokenBreakdown> = agent_totals
        .into_iter()
        .map(|(name, (total, input, output, count))| {
            let percentage = if total_tokens > 0 {
                (total as f64 / total_tokens as f64) * 100.0
            } else {
                0.0
            };
            agentsight::TokenBreakdown {
                name,
                total_tokens: total,
                input_tokens: input,
                output_tokens: output,
                request_count: count,
                percentage,
            }
        })
        .collect();

    breakdown.sort_by(|a, b| b.total_tokens.cmp(&a.total_tokens));
    breakdown
}

/// Print human-readable summary output
fn print_human_readable(
    result: &TokenQueryResult,
    show_compare: bool,
    show_breakdown: bool,
) {
    // Main result
    println!(
        "{}共消耗 {} tokens。",
        result.period,
        format_tokens_with_commas(result.total_tokens)
    );
    
    // Comparison
    if show_compare {
        if let Some(ref comp) = result.comparison {
            let trend = match comp.trend {
                Trend::Up => "增长",
                Trend::Down => "下降",
                Trend::Flat => "持平",
            };
            
            println!(
                "比上一时段（{}）{}了 {}。",
                format_tokens_with_commas(comp.previous_total),
                trend,
                comp.formatted_change()
            );
        }
    }
    
    // Breakdown
    if show_breakdown && !result.breakdown.is_empty() {
        println!();
        println!("主要消耗来源：");
        for item in &result.breakdown {
            println!(
                "- {}：{} tokens ({:.0}%)",
                item.name,
                format_tokens_with_commas(item.total_tokens),
                item.percentage
            );
        }
    }
    
    // Additional details
    if result.request_count > 0 {
        println!();
        println!(
            "共 {} 次请求，输入 {} tokens，输出 {} tokens。",
            result.request_count,
            format_tokens_with_commas(result.input_tokens),
            format_tokens_with_commas(result.output_tokens)
        );
    }
}

/// Print human-readable detail output for token consumption breakdown
fn print_detail_human_readable(result: &TokenConsumptionQueryResult, show_records: bool) {
    println!("=== Token 消耗明细 ({}) ===", result.period);
    println!("共 {} 条记录", result.record_count);
    println!();

    println!("输入 tokens：{}", format_tokens_with_commas(result.total_input_tokens));
    println!("输出 tokens：{}", format_tokens_with_commas(result.total_output_tokens));
    println!("总计 tokens：{}", format_tokens_with_commas(result.total_tokens));
    println!();

    if result.tools_tokens > 0 {
        println!("工具定义占用：{} tokens", format_tokens_with_commas(result.tools_tokens));
    }
    if result.system_prompt_tokens > 0 {
        println!("系统提示占用：{} tokens", format_tokens_with_commas(result.system_prompt_tokens));
    }

    if !result.by_role.is_empty() {
        println!();
        println!("按角色分布（输入）：");
        let mut roles: Vec<_> = result.by_role.iter().collect();
        roles.sort_by(|a, b| b.1.cmp(a.1));
        for (role, tokens) in roles {
            println!("  {:<12} {}", role, format_tokens_with_commas(*tokens));
        }
    }

    if !result.output_by_type.is_empty() {
        println!();
        println!("按类型分布（输出）：");
        let mut types: Vec<_> = result.output_by_type.iter().collect();
        types.sort_by(|a, b| b.1.cmp(a.1));
        for (typ, tokens) in types {
            println!("  {:<12} {}", typ, format_tokens_with_commas(*tokens));
        }
    }

    if show_records && !result.records.is_empty() {
        println!();
        println!("--- 明细记录 ---");
        for rec in &result.records {
            use std::time::{Duration, UNIX_EPOCH};
            let ts = UNIX_EPOCH + Duration::from_nanos(rec.timestamp_ns);
            let datetime = chrono::DateTime::<chrono::Utc>::from(ts).with_timezone(&chrono::Local);
            println!(
                "[{}] pid={} comm={} provider={} model={} in={} out={}",
                datetime.format("%Y-%m-%d %H:%M:%S"),
                rec.pid,
                rec.comm,
                rec.provider,
                rec.model,
                format_tokens_with_commas(rec.total_input_tokens as u64),
                format_tokens_with_commas(rec.total_output_tokens as u64),
            );
            let by_role = rec.by_role();
            if !by_role.is_empty() {
                let mut roles: Vec<_> = by_role.iter().collect();
                roles.sort_by(|a, b| b.1.cmp(a.1));
                let role_str: Vec<String> = roles.iter()
                    .map(|(r, t)| format!("{}:{}", r, t))
                    .collect();
                println!("  角色: {}", role_str.join(", "));
            }
        }
    }
}

