import streamlit as st
import json
import os

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")

CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
MODEL_CONFIG_PATH = os.path.join(CONFIG_DIR, "model.json")


def load_config(file_path):
    """安全加载 JSON 配置文件，不存在或解析失败则返回 {}"""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(config, file_path):
    """保存配置为 JSON 文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def run_streamlit_app():
    st.set_page_config(page_title="QFurina 配置", layout="wide")
    st.title("QFurina 配置（云端版，仅编辑 JSON）")

    # 直接从本项目的 config 目录加载配置
    config = load_config(CONFIG_PATH)
    model_config = load_config(MODEL_CONFIG_PATH)

    if "models" not in model_config:
        model_config["models"] = {}

    section = st.sidebar.radio("选择配置部分", ["基础配置", "模型配置", "系统消息", "插件配置", "导出配置"])

    # ---------- 基础配置 ----------
    if section == "基础配置":
        st.header("基础配置")
        col1, col2 = st.columns(2)
        with col1:
            config["api_key"] = st.text_input("API Key", config.get("api_key", ""))
            config["model"] = st.text_input(
                "模型名称(可选，默认 gpt-3.5-turbo)",
                config.get("model", "gpt-3.5-turbo"),
            )
            config["self_id"] = st.number_input(
                "Self ID（机器人 QQ 号）", value=config.get("self_id", 0)
            )
        with col2:
            config["admin_id"] = st.number_input(
                "Admin ID（管理员 QQ 号）", value=config.get("admin_id", 0)
            )

            # 回复概率，保证是 0~1 的 float
            raw_reply_prob = config.get("reply_probability", 0.024)
            try:
                reply_prob = float(raw_reply_prob)
            except (TypeError, ValueError):
                reply_prob = 0.024
            if not (0.0 <= reply_prob <= 1.0):
                reply_prob = 0.024

            config["reply_probability"] = st.slider(
                "回复概率（越接近1，回复概率越高，1为必定回复，0为必定不回复）",
                min_value=0.0,
                max_value=1.0,
                value=reply_prob,
            )

        config["r18"] = st.select_slider(
            "色图接口 R18 级别（0=非R18，1=允许R18，2=随机）",
            options=[0, 1, 2],
            value=config.get("r18", 2),
        )

        config["base_url"] = st.text_input(
            "Base URL (可选)",
            config.get("base_url", "https://api.openai.com/v1"),
        )

    # ---------- 模型配置 ----------
    elif section == "模型配置":
        st.header("模型配置（非 GPT 模型）")
        model_types = list(model_config.get("models", {}).keys())

        if not model_types:
            st.warning("当前没有任何模型配置，请先在 model.json 中添加 models 字段。")
        else:
            selected_model_type = st.selectbox("选择模型类型", model_types)
            if selected_model_type:
                st.subheader(f"{selected_model_type} 配置")
                model_details = model_config["models"].get(selected_model_type, {})

                col1, col2 = st.columns(2)
                with col1:
                    model_details["api_key"] = st.text_input(
                        f"{selected_model_type} API Key",
                        model_details.get("api_key", ""),
                    )
                with col2:
                    model_details["base_url"] = st.text_input(
                        f"{selected_model_type} Base URL",
                        model_details.get("base_url", ""),
                    )

                available_models = model_details.get("available_models", [])
                if available_models:
                    selected_model = st.selectbox(
                        f"选择 {selected_model_type} 模型",
                        available_models,
                        index=0,
                    )
                    if selected_model:
                        model_details["model"] = selected_model

                model_config["models"][selected_model_type] = model_details

    # ---------- 系统消息 ----------
    elif section == "系统消息":
        st.header("系统消息")
        config["system_message"] = config.get("system_message", {})
        config["system_message"]["character"] = st.text_area(
            "角色设定",
            config["system_message"].get("character", ""),
            height=300,
        )
        st.info("这里的设定会直接写入 config/config.json -> system_message.character")

    # ---------- 插件配置 ----------
    elif section == "插件配置":
        st.header("插件配置")
        all_plugins = config.get("enabled_plugins", [])
        # 为了方便，在这里允许手动输入全部插件列表
        raw = st.text_input(
            "全部可用插件名（逗号分隔，可留空）",
            ",".join(all_plugins) if all_plugins else "",
            help="例如：example,ai_drawing,weather,at_only,deepseek_chat",
        )
        if raw.strip():
            all_plugins = [x.strip() for x in raw.split(",") if x.strip()]
        enabled_plugins = st.multiselect(
            "启用的插件",
            all_plugins,
            default=all_plugins,
        )
        config["enabled_plugins"] = enabled_plugins
        st.info("这里选择的列表会写入 config/config.json -> enabled_plugins")

    # ---------- 导出配置 ----------
    elif section == "导出配置":
        st.header("导出当前 config.json")
        pretty_json = json.dumps(config, ensure_ascii=False, indent=4)
        st.code(pretty_json, language="json")
        st.download_button(
            "下载 config.json",
            data=pretty_json.encode("utf-8"),
            file_name="config.json",
            mime="application/json",
        )

    # ---------- 保存按钮 ----------
    if st.button("保存配置到云端容器"):
        save_config(config, CONFIG_PATH)
        save_config(model_config, MODEL_CONFIG_PATH)
        st.success("已保存到该 Streamlit 容器的 config/config.json 和 config/model.json")


if __name__ == "__main__":
    run_streamlit_app()
