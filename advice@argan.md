*** ok, here is another response, this one uses the actual email address forwarder I will be using in my app as it's coming from the email account that my client is actually using and forwarding from (ie advice@arganhrconsultancy.co.uk). Give me those fields as a definitive list and just highlight any differences between this one and the previous example that was forwarded from Hostinger so I can see any examples of how things might differ from one forwarder to another. ***

🚀 RAW SENDGRID WEBHOOK PAYLOAD - NO PARSING
====================================================================================================
📅 Timestamp: 2025-06-03T04:43:24.997752
📏 Content Length: 8204 bytes
📦 Content Type: multipart/form-data; boundary=xYzZY

📋 REQUEST HEADERS:
   host: a8bc-86-163-177-54.ngrok-free.app
   user-agent: Sendlib/1.0
   content-length: 8204
   accept-encoding: gzip
   content-type: multipart/form-data; boundary=xYzZY
   x-forwarded-for: 167.89.119.32
   x-forwarded-host: a8bc-86-163-177-54.ngrok-free.app
   x-forwarded-proto: https

🔢 RAW BYTES (first 50):
   b'--xYzZY\r\nContent-Disposition: form-data; name="hea'

📄 RAW DECODED STRING (COMPLETE - NO PARSING):
--xYzZY
Content-Disposition: form-data; name="headers"

Content-Transfer-Encoding: quoted-printable
Content-Type: text/plain; charset=utf-8
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;        d=gmail.com; s=20230601; t=1748925782; x=1749530582; darn=arganhrconsultancy.co.uk;        h=to:date:message-id:subject:mime-version:content-transfer-encoding         :from:from:to:cc:subject:date:message-id:reply-to;        bh=CEFjZXevil93deLhLlkKrNP1ovhZi+nSiz4ZxQzRLT8=;        b=JCDAea097NZuAf4chbjqgUOlyH6+G/4VLviNX0t8CUNIK0FASQ6Cj5uvC+SAvYww0e         pPoCsrKqLWINKHXy8p0M4Py8/SzfAm43hbMKHmiaQo9fjRreV6SOKNxmvfgBzWUs+Bnr         wY090VBDgQQOfQqowmEZxMKcJUxQll3GN+wcBQV2bDubMUjM+tPbz9BX1zp9r2v1qyoN         PZHRRl+cONeY67Gb8zaj6cdUTjpc8RIiDvITgCe/x9PGlSBKxaaimZehaYutlTsKcX39         fQtTj68olQdUBwHMm99gYxZ7G1EBt0a4z9NeFrG6Y5+g/UbsRyDgodGiodkA4d+JtyE5         9reQ==
Date: Tue, 3 Jun 2025 05:42:51 +0100
From: cvrcontractsltd <cvrcontractsltd@gmail.com>
Message-Id: <256304D3-3BE0-4EC0-91A0-EF12F7C3463C@gmail.com>
Mime-Version: 1.0 (Mac OS X Mail 16.0 \(3774.300.61.1.2\))
Received: from mout.kundenserver.de (mxd [212.227.126.135]) by mx.sendgrid.net with ESMTP id na9XiRFCTw2Tap3_fUie-g for <email@email.adaptixinnovation.co.uk>; Tue, 03 Jun 2025 04:43:24.518 +0000 (UTC)
Received: from mail-wm1-f42.google.com ([209.85.128.42]) by mx.kundenserver.de (mxeue002 [212.227.15.41]) with ESMTPS (Nemesis) id 1MBC3y-1u9cS100oI-00ABph for <advice@arganhrconsultancy.co.uk>; Tue, 03 Jun 2025 06:43:03 +0200
Received: by mail-wm1-f42.google.com with SMTP id 5b1f17b1804b1-451d7b50815so15495635e9.2        for <advice@arganhrconsultancy.co.uk>; Mon, 02 Jun 2025 21:43:02 -0700 (PDT)
Received: from smtpclient.apple (host86-163-177-54.range86-163.btcentralplus.com. [86.163.177.54])        by smtp.gmail.com with ESMTPSA id 5b1f17b1804b1-450d7f8edc0sm143952695e9.5.2025.06.02.21.43.01        for <advice@arganhrconsultancy.co.uk>        (version=TLS1_2 cipher=ECDHE-ECDSA-AES128-GCM-SHA256 bits=128/128);        Mon, 02 Jun 2025 21:43:01 -0700 (PDT)
Return-Path: <cvrcontractsltd@gmail.com>
Subject: Test email subject…advice
To: advice@arganhrconsultancy.co.uk
UI-Loop: V01:UuztV6PCc2c=:OySG5n0FMCFrJ8PVzqKXmnT34CYFFu4sbvtDqWqJuKM=
UI-OutboundReport: notjunk:1;M01:P0:gUbkRLbZehE=;VWVJ2czGdc7J1B5ljYLmMQMtnCc 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
X-Gm-Gg: ASbGncvPa0rwQPJWKMQ6PfY1/Q4FDeDX70vvD8pDvJhtl2ehcH1OZHrnloBQ3JBMtJ2    xc5p9erCE1dOD0zXkTiLWDGjuf5n6iheRVazDBbE8OkHRB1zxLhz+K9Vk6JVdvhbQKsLvrPFtn+       9QUz1XTHjkCsQdN4DcqDJgoErYFo1Z+WXYNDJVSIDcL9fP7wu/pGp2OWZwayFpoRb33USBFKqMx       IdWj5HEj7CAbdJPrMqPNxrJT3KQBYiXGtiJ28xuGNXWfuXpiyfoZFdVhzJONBt+7U/PS4A8SoX3       Rk2GAGkLnsHKF4jFxGXEzQQW3PjVCOLN7iDhnUDF7p5GVlwAlpGZiGU/HV6dxgjzKsgC8mKv+//       CUlxIeSyWsx6eZVqlpJ7YDo9UjIu0iVh1P/HQM7oHiPyiezZbMGN0yg==
X-Gm-Message-State: AOJu0Yzhrj6HCxp4B5DYguC8rYznBtlaehs9rGd0VN9aqCuiOE2sC1DY    qkeO7LI73KOyprbLocpDehhO+ZEUMgaPYaEgU7lpsE1ZqxTd1gziFR6iTE8XBA==
X-Google-DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;        d=1e100.net; s=20230601; t=1748925782; x=1749530582;        h=to:date:message-id:subject:mime-version:content-transfer-encoding         :from:x-gm-message-state:from:to:cc:subject:date:message-id:reply-to;        bh=CEFjZXevil93deLhLlkKrNP1ovhZi+nSiz4ZxQzRLT8=;        b=IEYIMiDWdLCxvS51FZ/47cW7fIPKofMfAUFs2DoCeAsgkzfsBT9QgkB7h9lEAyS6SO         hlwQ3Y1oyKdISNA2yf2JuOPQsyx8t17RZkgpUMQ8W2G6Ms34OLMIPppPnYowQ0mC6sgD         kTdNX54sMMY4oVVmEt0N+tIaFd2wLHE5X1oje9FQMD051mvnVaYpaLm0P3vh8LcjgAl8         nD6XpZYzpTmYBNWQsjtzFGEZHuN+4TbQlfc6iSsRq81kMQz5wV01dYjm7MCfbTqBqvLb         TBTEP/BGW5e7lNdyGssSTyIqlfyfQ8KzRdZqqKwPS9fdqAFuUE5qvmE8On6zzkqHb6mt         sFmQ==
X-Google-Smtp-Source: AGHT+IHQm67i6IPOPY2hbeTnuy3/29uhkj7sl8zvqsaeFRjo25EAYsO3vq9S17UhLFdbgmuDebpgjg==
X-Mailer: Apple Mail (2.3774.300.61.1.2)
X-Received: by 2002:a05:6000:2303:b0:3a4:da87:3a73 with SMTP id ffacd0b85a97d-3a4f89dcc3amr10394575f8f.42.1748925782291;        Mon, 02 Jun 2025 21:43:02 -0700 (PDT)
X-Spam-Flag: NO

--xYzZY
Content-Disposition: form-data; name="sender_ip"

212.227.126.135
--xYzZY
Content-Disposition: form-data; name="SPF"

pass
--xYzZY
Content-Disposition: form-data; name="to"

advice@arganhrconsultancy.co.uk
--xYzZY
Content-Disposition: form-data; name="subject"

Test email subject…advice
--xYzZY
Content-Disposition: form-data; name="text"

Test email body…advice
--xYzZY
Content-Disposition: form-data; name="attachments"

0
--xYzZY
Content-Disposition: form-data; name="charsets"

{"to":"UTF-8","from":"UTF-8","subject":"UTF-8","text":"utf-8"}
--xYzZY
Content-Disposition: form-data; name="dkim"

{@gmail.com : pass}
--xYzZY
Content-Disposition: form-data; name="from"

cvrcontractsltd <cvrcontractsltd@gmail.com>
--xYzZY
Content-Disposition: form-data; name="envelope"

{"to":["email@email.adaptixinnovation.co.uk"],"from":"advice@arganhrconsultancy.co.uk"}
--xYzZY--


====================================================================================================
INFO:     167.89.119.32:0 - "POST /webhook/inbound HTTP/1.1" 200 OK