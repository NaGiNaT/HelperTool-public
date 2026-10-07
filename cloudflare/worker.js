export default {
  async fetch(request, env) {
    if (request.method === "GET") {
      return new Response("helpertool");
    }
    if (request.method !== "POST") {
      return new Response("method", { status: 405 });
    }

    const secret = env.APP_SECRET || "";
    const header = request.headers.get("Authorization") || "";
    if (!secret || header !== `Bearer ${secret}`) {
      return new Response("unauthorized", { status: 401 });
    }

    try {
      const job = await readJob(request);
      if (job.action === "tg_log") {
        await sendTelegramLog(env, job.text);
        return Response.json({ ok: true });
      }
      if (job.action === "vk_message") {
        await sendVk(env, job.peerId, job.text, job.photo, job.filename);
        return Response.json({ ok: true });
      }
      return new Response("unknown action", { status: 400 });
    } catch (error) {
      const message = error && error.message ? error.message : String(error);
      return new Response(message, { status: 500 });
    }
  },
};

async function readJob(request) {
  const contentType = request.headers.get("Content-Type") || "";
  if (contentType.includes("multipart/form-data")) {
    const form = await request.formData();
    const photo = form.get("photo");
    let bytes = null;
    let filename = "screenshot.png";
    if (photo && typeof photo.arrayBuffer === "function") {
      bytes = await photo.arrayBuffer();
      filename = photo.name || filename;
    }
    return {
      action: String(form.get("action") || ""),
      text: String(form.get("text") || ""),
      peerId: String(form.get("peer_id") || ""),
      photo: bytes,
      filename,
    };
  }

  const body = await request.json();
  return {
    action: String(body.action || ""),
    text: String(body.text || ""),
    peerId: String(body.peer_id || ""),
    photo: null,
    filename: "screenshot.png",
  };
}

async function sendTelegramLog(env, text) {
  const response = await fetch(
    `https://api.telegram.org/bot${env.TELEGRAM_REDIR_BOT_TOKEN}/sendMessage`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: env.LOG_CHAT_ID,
        text,
        parse_mode: "HTML",
      }),
    }
  );
  const data = await response.json();
  if (!data.ok) {
    throw new Error("telegram log failed");
  }
}

async function sendVk(env, peerId, message, photoBytes, filename) {
  const attachment = photoBytes
    ? await uploadVkPhoto(env, peerId, photoBytes, filename)
    : "";
  const data = await vkCall(env, "messages.send", {
    peer_id: peerId,
    random_id: String(Math.floor(Math.random() * 1_000_000_000)),
    message,
    attachment,
  });
  if (data.error) {
    throw new Error("vk send failed");
  }
}

async function uploadVkPhoto(env, peerId, photoBytes, filename) {
  const server = await vkCall(env, "photos.getMessagesUploadServer", { peer_id: peerId });
  if (!server.response || !server.response.upload_url) {
    throw new Error("vk upload server failed");
  }

  const form = new FormData();
  form.append("photo", new Blob([photoBytes], { type: "image/png" }), filename);
  const uploaded = await fetch(server.response.upload_url, { method: "POST", body: form });
  const uploadedData = await uploaded.json();

  const saved = await vkCall(env, "photos.saveMessagesPhoto", {
    photo: uploadedData.photo,
    server: String(uploadedData.server),
    hash: uploadedData.hash,
  });
  const photo = saved.response && saved.response[0];
  if (!photo) {
    throw new Error("vk save photo failed");
  }
  return `photo${photo.owner_id}_${photo.id}`;
}

async function vkCall(env, method, fields) {
  const body = new URLSearchParams({
    access_token: env.VK_TOKEN,
    v: "5.199",
  });
  for (const [key, value] of Object.entries(fields)) {
    if (value) {
      body.set(key, value);
    }
  }
  const response = await fetch(`https://api.vk.com/method/${method}`, {
    method: "POST",
    body,
  });
  return response.json();
}
