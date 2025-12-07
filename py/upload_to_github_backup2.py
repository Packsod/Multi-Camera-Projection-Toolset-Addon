import os
import bpy
import requests
import json
import base64

# List of supported file extensions
SUPPORTED_EXTENSIONS = ['.py', '.toml']

# List of field names
FIELDS = [
    "commit_title",
    "commit_message",
    "github_token",
    "repo_owner",
    "repo_name",
    "branch_name",
    "author_name",
    "email_address"
]

# repo_config.json template
CONFIG_TEMPLATE = {field: "" for field in FIELDS}

class ConfigManager:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(bpy.data.filepath), 'repo_config.json')
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            with open(self.config_path, 'w') as f:
                json.dump(CONFIG_TEMPLATE, f, indent=4)
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value
        self.save_config()

config_manager = ConfigManager()

def get_github_headers(token=None):
    token = token or config_manager.get('github_token')
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

def file_content_is_same_on_github(relative_file_path):
    url = f"https://api.github.com/repos/{config_manager.get('repo_owner')}/{config_manager.get('repo_name')}/contents/{relative_file_path}?ref={config_manager.get('branch_name')}"
    headers = get_github_headers()
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return False  # File does not exist or request failed, assume different (need to upload)
    github_data = r.json()
    if 'content' not in github_data:
        return False
    github_content = base64.b64decode(github_data['content'].replace('\n', ''))

    # Normalize both to LF line endings before comparison
    local_file_path = os.path.join(os.path.dirname(bpy.data.filepath), relative_file_path)
    with open(local_file_path, 'rb') as f:
        local_content = f.read()
    local_content = local_content.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    github_content = github_content.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    return local_content == github_content

def update_py_file_on_github(relative_file_path, file_content):
    url = f"https://api.github.com/repos/{config_manager.get('repo_owner')}/{config_manager.get('repo_name')}/contents/{relative_file_path}"
    headers = get_github_headers()

    # Get remote sha
    r = requests.get(url + f"?ref={config_manager.get('branch_name')}", headers=headers)
    if r.status_code == 200:
        github_data = r.json()
        sha = github_data['sha']
    else:
        sha = None

    commit_title = config_manager.get('commit_title') or "Update file"
    commit_message = config_manager.get('commit_message')
    payload = {
        "message": f"{commit_title}\n\n{commit_message}",
        "content": base64.b64encode(file_content).decode('utf-8'),
        "branch": config_manager.get('branch_name'),
        "committer": {
            "name": config_manager.get('author_name'),
            "email": config_manager.get('email_address'),
        }
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, data=json.dumps(payload))
    return resp.status_code, resp.text

class REPOUPLOAD_OT_ConfigDialog(bpy.types.Operator):
    bl_idname = "repoupload.config_dialog"
    bl_label = "GitHub Upload Configuration"

    # Generate configuration properties
    for field in FIELDS:
        exec(f"{field}: bpy.props.StringProperty(name='{field.capitalize()}')")

    def invoke(self, context, event):
        for field in FIELDS:
            setattr(self, field, config_manager.get(field, ""))

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        # Enable property splitting and decoration
        layout.use_property_split = True
        layout.use_property_decorate = False
        for field in FIELDS:
            layout.prop(self, field)
        # 新增撤回按钮
        layout.operator("repoupload.revert_last_commit", text="Revert Last Commit")

    def execute(self, context):
        for field in FIELDS:
            config_manager[field] = getattr(self, field)

        try:
            addon_folder = os.path.dirname(bpy.data.filepath)
            files_to_upload = []
            for root, _, files in os.walk(addon_folder):
                # Calculate relative path and unify separator to /
                relative_path = os.path.relpath(root, addon_folder).replace(os.sep, '/')
                for file in files:
                    if any(file.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                        relative_file_path = os.path.join(relative_path, file).replace(os.sep, '/')
                        if not file_content_is_same_on_github(relative_file_path):
                            files_to_upload.append(relative_file_path)

            if not files_to_upload:
                def draw_message(self, context):
                    layout = self.layout
                    layout.label(text="No files need to be uploaded.")

                bpy.context.window_manager.popup_menu(draw_message, title="Upload Result", icon='INFO')
            else:
                # Continue with the rest of the upload process
                for file_path in files_to_upload:
                    local_file_path = os.path.join(os.path.dirname(bpy.data.filepath), file_path)
                    with open(local_file_path, 'rb') as f:
                        file_content = f.read()
                    # Normalize line endings to LF
                    file_content = file_content.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
                    status, msg = update_py_file_on_github(file_path, file_content)
                    print(f"File: {file_path}, Status: {status}, Message: {msg}")

                print("Files uploaded successfully to GitHub.")
                def draw_message(self, context):
                    layout = self.layout
                    layout.label(text="Upload completed!")
                    for file_path in files_to_upload:
                        layout.label(text=file_path)

                bpy.context.window_manager.popup_menu(draw_message, title="Upload Result", icon='INFO')


        except requests.exceptions.SSLError as e:
            def draw_error(self, context):
                layout = self.layout
                layout.label(text="SSLError, please try again.")
                layout.label(text=str(e))

            bpy.context.window_manager.popup_menu(draw_error, title="Error", icon='ERROR')

        except Exception as e:
            def draw_error(self, context):
                layout = self.layout
                layout.label(text="Upload failed, possibly due to incorrect form filling.")
                layout.label(text=str(e))

            bpy.context.window_manager.popup_menu(draw_error, title="Error", icon='ERROR')

        return {'FINISHED'}

# 新增：撤回最近一次提交的操作
class REPOUPLOAD_OT_RevertLastCommit(bpy.types.Operator):
    bl_idname = "repoupload.revert_last_commit"
    bl_label = "Revert Last Commit"

    def execute(self, context):
        try:
            # 获取最近一次提交
            commits_url = f"https://api.github.com/repos/{config_manager.get('repo_owner')}/{config_manager.get('repo_name')}/commits?sha={config_manager.get('branch_name')}"
            headers = get_github_headers()
            r = requests.get(commits_url, headers=headers)
            if r.status_code != 200:
                raise Exception(f"Failed to get commits: {r.text}")

            commits = r.json()
            if not commits:
                raise Exception("No commits found on the branch")

            last_commit = commits[0]
            parent_commit_sha = last_commit['parents'][0]['sha']

            # 获取父提交的树
            parent_commit_url = f"https://api.github.com/repos/{config_manager.get('repo_owner')}/{config_manager.get('repo_name')}/commits/{parent_commit_sha}"
            r = requests.get(parent_commit_url, headers=headers)
            if r.status_code != 200:
                raise Exception(f"Failed to get parent commit: {r.text}")

            parent_commit = r.json()
            tree_sha = parent_commit['commit']['tree']['sha']

            # 创建新的提交（撤回）
            create_commit_url = f"https://api.github.com/repos/{config_manager.get('repo_owner')}/{config_manager.get('repo_name')}/git/commits"
            payload = {
                "message": f"Revert: {last_commit['commit']['message']}",
                "tree": tree_sha,
                "parents": [last_commit['sha']]
            }
            r = requests.post(create_commit_url, headers=headers, data=json.dumps(payload))
            if r.status_code != 201:
                raise Exception(f"Failed to create revert commit: {r.text}")

            new_commit_sha = r.json()['sha']

            # 更新分支引用
            update_ref_url = f"https://api.github.com/repos/{config_manager.get('repo_owner')}/{config_manager.get('repo_name')}/git/refs/heads/{config_manager.get('branch_name')}"
            payload = {"sha": new_commit_sha}
            r = requests.patch(update_ref_url, headers=headers, data=json.dumps(payload))
            if r.status_code != 200:
                raise Exception(f"Failed to update branch reference: {r.text}")

            self.report({'INFO'}, "Successfully reverted the last commit")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Revert failed: {str(e)}")
            return {'CANCELLED'}

# 新增：面板，包含配置按钮和撤回按钮
class REPOUPLOAD_PT_Panel(bpy.types.Panel):
    bl_label = "GitHub Upload Panel"
    bl_idname = "REPOUPLOAD_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GitHub Upload'

    def draw(self, context):
        layout = self.layout
        layout.operator("repoupload.config_dialog", text="Configure")
        layout.operator("repoupload.revert_last_commit", text="Revert Last Commit")

def register():
    bpy.utils.register_class(REPOUPLOAD_OT_ConfigDialog)
    bpy.utils.register_class(REPOUPLOAD_OT_RevertLastCommit)
    bpy.utils.register_class(REPOUPLOAD_PT_Panel)
    bpy.ops.repoupload.config_dialog('INVOKE_DEFAULT')

def unregister():
    bpy.utils.unregister_class(REPOUPLOAD_OT_ConfigDialog)
    bpy.utils.unregister_class(REPOUPLOAD_OT_RevertLastCommit)
    bpy.utils.unregister_class(REPOUPLOAD_PT_Panel)

if __name__ == "__main__":
    register()
